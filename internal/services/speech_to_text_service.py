from google.cloud import speech

import threading

from typing import Function

import queue

class SpeechToTextService:
    def __init__(self, on_response: Function) -> None:
        self._ended = True
        self._on_response = on_response

    def start(self):
        self._ended = False

        client = speech.SpeechClient()
        stream = self.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
            sample_rate_hertz=8000,
            language_code="en-US",
        )

        streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

        responses = client.streaming_recognize(
            config=streaming_config,
            requests=requests,
        )

        self.process_responses_loop(responses)

    def process_responses_loop(self, responses):
        for response in responses:
            self._on_response(response)

            if self._ended:
                break

    def terminate(self):
        self._ended = True

    def get_process_thread(self):
        return threading.Thread(target=self.start)

    def get_generator(self, decode_queue: queue.Queue):
        while not self._ended:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = decode_queue.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while not decode_queue.empty():
                try:
                    chunk = decode_queue.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

