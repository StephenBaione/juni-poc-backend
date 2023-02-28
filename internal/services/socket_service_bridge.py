import queue

from google.cloud import speech

import threading

class SpeechClientBridge:
    def __init__(self, on_response, decode_queue):
        self._on_response = on_response
        self._queue = queue.Queue()
        self._ended = False
        self.decode_queue = decode_queue
        self.stream_sid = None

    def start(self):
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

    def terminate(self):
        self._ended = True

    def add_request(self, buffer):
        self._queue.put(bytes(buffer), block=False)

    def process_responses_loop(self, responses):
        for response in responses:
            self._on_response(response, self.decode_queue)

            if self._ended:
                break

    def generator(self):
        while not self._ended:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._queue.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._queue.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

