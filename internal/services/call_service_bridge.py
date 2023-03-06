from client_service_bridge import ClientServiceBridge
from speech_to_text_service import SpeechToTextService
from text_to_speech_service import TextToSpeechService
from openai_api import OpenAIClient

import queue
from fastapi import WebSocket

import asyncio

import base64
import time

class CallServiceBridge(ClientServiceBridge):
    def __init__(
        self, 
        rcv_queue: queue.Queue, 
        result_queue: queue.Queue, 
        websocket: WebSocket, 
        speech_to_text_service: SpeechToTextService, 
        text_to_speech_service: TextToSpeechService,
        openai_client: OpenAIClient,
        receiver_event: asyncio.Event,
        sender_event: asyncio.Event,
        kill_event: asyncio.Event
    ) -> None:
        super().__init__(rcv_queue, result_queue, websocket, None)

        self.speech_to_text_service = speech_to_text_service
        self.text_to_speech_service = text_to_speech_service
        self.openai_client = openai_client

        self.speech_to_text_decode_queue = queue.Queue()
        self.last_transcription = None

        # Enabled us to track stream when sending data back to twilio
        self.stream_sid = None

        self.speech_to_text_thread = None

        self.receiver_event = receiver_event
        self.sender_event = sender_event
        self.kill_event = kill_event

    def process_message(self, message) -> bool:
        # Process message
        if message is None:
            self.rcv_queue.put(None)
        if message.get('type', '') == 'websocket.connect':
            return True
        elif message.get('event', '') == 'connected':
            return True
        elif message.get('event', '') == 'start':
            self.stream_sid = message['streamSid']
            return True

        elif message.get('event', '') == 'media':
            media = message["media"]
            if media['payload'] is None:
                raise ValueError('No payload in media message')
            chunk = base64.b64decode(media["payload"])
            self.add_receiver_request(chunk)
            return True

    def check_transcription(self):
        if not self.speech_to_text_decode_queue.empty():
            last_transcription = self.speech_to_text_decode_queue.get(block=False)
            if last_transcription == '||TALKING||':
                return

            self.result_queue.put(last_transcription)
            self.last_transcription = time.time()

    def ensure_empty_decode_queue(self):
        while not self.speech_to_text_decode_queue.empty():
            last_transcription = self.speech_to_text_decode_queue.get(block=False)
            if last_transcription == '||TALKING||':
                continue

            self.result_queue.put(last_transcription)

    async def listen_loop(self):
        kill_event = self.kill_event
        receiver_event = self.receiver_event
        sender_event = self.sender_event

        while not kill_event.is_set():
            while not receiver_event.is_set():
                message = await self.websocket.receive()

                # Start transcription if it hasn't started
                if self.speech_to_text_service._ended:
                    print('start transcription')
                    speech_to_text_thread = self.speech_to_text_service.get_process_thread()
                    speech_to_text_thread.start()

                end = self.process_message(message)
                if end:
                    break

                self.check_transcription()

                now = time.time()
                if self.last_transcription is not None and \
                now - self.last_transcription > 2:
                    break

            receiver_event.set()
            await sender_event.wait()
            sender_event.clear()

    async def process_loop(self):
        kill_event = self.kill_event
        receiver_event = self.receiver_event
        sender_event = self.sender_event

        while not kill_event.is_set():
            await receiver_event.wait()

            while not sender_event.is_set():
                if not self.rcv_queue.empty():
                    message = self.rcv_queue.get()
                    if message is None:
                        break

                    self.service.process(message)
            
    async def send_loop(self):
        kill_event = self.kill_event
        receiver_event = self.receiver_event
        sender_event = self.sender_event

        while not kill_event.is_set():
            await receiver_event.wait()
            receiver_event.clear()

            while not sender_event.is_set():
                if not self.result_queue.empty():
                    result = self.result_queue.get()
                    if result is None:
                        break

                await self.websocket.send_text(result)
            
            sender_event.set()

    def add_receiver_request(self, message):
        if message is None:
            self.rcv_queue.put(None, block=False)

        self.rcv_queue.put(bytes(message), block=False)
