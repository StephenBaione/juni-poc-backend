from .client_service_bridge import ClientServiceBridge
from .speech_to_text_service import SpeechToTextService
from .text_to_speech_service import TextToSpeechService
from .openai_service import OpenAIClient

import queue
from fastapi import WebSocket

import asyncio

import base64
import time

class CallServiceBridge(ClientServiceBridge):
    def __init__(
        self,
        websocket: WebSocket
    ) -> None:
        rcv_queue = queue.Queue()
        result_queue = queue.Queue()

        super().__init__(rcv_queue, result_queue, websocket, None)

        self.last_transcription = None
        self.service_queue = queue.Queue()
        self.speech_to_text_service = SpeechToTextService(
            self.on_transcription_response,
            self.service_queue
        )

        self.text_to_speech_service = TextToSpeechService()
        self.openai_client = OpenAIClient()

        # Enabled us to track stream when sending data back to twilio
        self.stream_sid = None

        self.speech_to_text_thread = None

        self.receiver_event = asyncio.Event()
        self.sender_event = asyncio.Event()
        self.kill_event = asyncio.Event()

        self.last_decode_time = None

        self.transcription = ''

    def process_message(self, message) -> bool:
        # Process message
        if message is None:
            self.rcv_queue.put(None)
        if message.get('type', '') == 'websocket.connect':
            return True

        elif message.get('event', '') == 'media':
            media = message["media"]
            if media['payload'] is None:
                raise ValueError('No payload in media message')
            chunk = base64.b64decode(media["payload"])
            self.add_receiver_request(chunk)
            return True

    def check_transcription(self):
        if not self.service_queue.empty():
            last_transcription = self.service_queue.get(block=False)
            if last_transcription == '||TALKING||':
                return

            self.result_queue.put(last_transcription)
            self.last_transcription = time.time()

    def ensure_empty_decode_queue(self):
        while not self.service_queue.empty():
            last_transcription = self.service_queue.get(block=False)
            if last_transcription == '||TALKING||':
                continue

            self.result_queue.put(last_transcription)

    def on_transcription_response(response, decode_queue: queue.Queue):
        if not response.results:
            return
        
        result = response.results[0]
        if not result.alternatives:
            return
        
        if result.is_final:
            transcription = result.alternatives[0].transcript
            if transcription != '':
                decode_queue.put(transcription, block=False)
        else:
            decode_queue.put('||TALKING||', block=False)

    async def listen_loop(self, timeout=1.5):
        kill_event = self.kill_event
        receiver_event = self.receiver_event
        sender_event = self.sender_event

        while not kill_event.is_set():
            print('Waiting for message')
            while not receiver_event.is_set():
                message = await self.websocket.receive()

                # Start transcription if it hasn't started
                if self.speech_to_text_service._ended:
                    print('start transcription')
                    speech_to_text_thread = self.speech_to_text_service.get_process_thread()
                    speech_to_text_thread.start()

                self.process_message(message)

                self.check_transcription()

                now = time.time()
                if self.last_transcription is not None and \
                now - self.last_transcription > timeout:
                    break

            receiver_event.set()
            await sender_event.wait()
            sender_event.clear()

    async def process_loop(self):
        kill_event = self.kill_event
        sender_event = self.sender_event

        while not kill_event.is_set():
            while not sender_event.is_set():
                if not self.rcv_queue.empty():
                    message = self.rcv_queue.get()
                    if message is None:
                        break

                    self.speech_to_text_service.add_request(message)
            
    async def send_loop(self):
        kill_event = self.kill_event
        receiver_event = self.receiver_event
        sender_event = self.sender_event

        while not kill_event.is_set():
            await receiver_event.wait()

            while not sender_event.is_set():
                if not self.result_queue.empty():
                    result = self.result_queue.get()
                    if result is None:
                        break

                await self.websocket.send_text(result)
            
            sender_event.set()
            receiver_event.clear()

    def add_receiver_request(self, message):
        if message is None:
            self.rcv_queue.put(None, block=False)

        self.rcv_queue.put(bytes(message), block=False)

    def terminate(self):
        self.kill_event.set()
        self.speech_to_text_service.terminate()
        self.speech_to_text_thread.join()

    def bi_directional_task(self):
        print('start bi-directional task')
        self.speech_to_text_thread = self.speech_to_text_service.get_process_thread()

        event_loop = asyncio.get_event_loop()
        listen_task = event_loop.create_task(self.listen_loop())
        send_task = event_loop.create_task(self.send_loop())

        self.sender_event.set()

        # Start both asynchronous tasks to run asynchronously
        self.speech_to_text_thread.start()
        print('STT thread started')
        event_loop.run_until_complete(asyncio.gather(listen_task, send_task))
        print('end bi-directional task')
