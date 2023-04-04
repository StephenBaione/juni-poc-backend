from __future__ import division

import sys
import os

import asyncio
import threading

from google.cloud import speech

from internal.clients.web_socket_client import WebSocketClient

import uuid

clients = {}


class SpeechClient(WebSocketClient):
    def __init__(self) -> None:
        self.speech_client = speech.SpeechClient.from_service_account_json(os.path.join('creds', 'google_speech_secret_key.json'))
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True
        )

        self.audio_generator = self.generator()
        self.client_id = uuid.uuid4()

        thread = threading.Thread(
            target=asyncio.run, args=(self.start_listening(), ))
        super().__init__(thread)

    async def start_listening(self):
        print('starting listening')
        self.start_thread()

    async def start_recognition_stream(self):
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in self.audio_generator)

        responses = self.speech_client.streaming_recognize(
            self.streaming_config, requests)

        await listen_print_loop(responses, self)

    async def stop_recognition_stream(self):
        self.disconnect()

    def receive_data(self, data):
        print('recieved data')
        self.write_to_buffer(data)

async def listen_print_loop(responses, speech_buffer: SpeechClient):
    num_chars_printed = 0
    interim_flush_counter = 0

    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            interim_flush_counter += 1

            if speech_buffer and interim_flush_counter % 3 == 0:
                interim_flush_counter = 0
                await speech_buffer.notify_listeners(transcript + overwrite_chars + '\r', False)

            num_chars_printed = len(transcript)

        else:
            text = transcript + overwrite_chars
            print(text)

            if speech_buffer:
                await speech_buffer.notify_listeners(text)

            num_chars_printed = 0


class SpeechRecognitionService:
    encoding_map = {
        'LINEAR16': speech.RecognitionConfig.AudioEncoding.LINEAR16}

    def __init__(self):
        self.speech_clients = {}

    @staticmethod
    def _get_google_stream_object(self):
        return {
            'client': speech.SpeechClient(),
            'config': speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True
            ),
            'streaming_config': speech.StreamingRecognitionConfig(
                config=self.config,
                interim_results=True
            )
        }

    async def start_listen(self, client_id):
        client: SpeechClient = self.get_client(client_id)
        if client is None:
            return

        audio_generator = client.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)
        responses = client.speech_client.streaming_recognize(
            client.streaming_config, requests)

        await listen_print_loop(responses, client)

    async def start_recognition_stream(self, client_id):
        if self.speech_clients.get(client_id, None) is not None:
            return None

        speech_client = SpeechClient()
        speech_client.start_listening()

    async def stop_recognition_stream(self, client_id):
        speech_client: SpeechClient = self.speech_clients.get(client_id, None)
        if speech_client is None:
            return None

        speech_client.disconnect()

    def get_client(self, client_id):
        return self.speech_clients.get(client_id, None)

    def add_client(self, client_id, client):
        self.speech_clients[client_id] = client

    def remove_client(self, client_id):
        client = self.speech_clients.pop(client_id, None)
        client.disconnect()

        return client

    def write_to_client(self, client_id, data):
        client = self.speech_clients.get(client_id, None)
        if client is None:
            return

        client.receive_data(data)


async def listen_print_loop(responses, client):
    print('start loop')
    num_chars_printed = 0
    interim_flush_counter = 0
    for response in responses:
        if not response.results:
            continue

        print('result')
        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        print('transcript', transcript)
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            interim_flush_counter += 1

            if client and interim_flush_counter % 3 == 0:
                interim_flush_counter = 0
                client.notify_listeners(
                    transcript + overwrite_chars + '\r', False)
                # await client.send_message(transcript + overwrite_chars + '\r', False)

            num_chars_printed = len(transcript)

        else:
            text = transcript + overwrite_chars
            client.notify_listeners(text)

            # if client:
            #     await client.send_client_data(text, True)

            num_chars_printed = 0
