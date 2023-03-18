from dotenv import load_dotenv
load_dotenv()

import html
from time import time
from uuid import uuid4

from azure.cognitiveservices.speech import SpeechRecognizer, SpeechConfig, SpeechSynthesizer, SpeechSynthesisResult, ResultReason, CancellationReason, PropertyId, ResultFuture, SpeechRecognitionCanceledEventArgs, SpeechRecognitionEventArgs, SessionEventArgs
from azure.cognitiveservices.speech.audio import AudioConfig, PullAudioOutputStream, PullAudioInputStream, PullAudioOutputStream, AudioOutputConfig, PushAudioInputStream
import azure.cognitiveservices.speech as azure_speechsdk

from internal.services.socket_service import SocketService

import asyncio

import io
import os
import json

from typing import Callable, Optional

from data.firebase.firebase_storage import FirebaseStorage

from internal.utilities.xml import XMLAttributes, XMLTag, XMLDoc

import enum
import queue

from pydantic import BaseModel

class AzureRecognitionCallbacks(BaseModel):
    recognizing: Optional[Callable] = None
    recognized: Optional[Callable] = None
    canceled: Optional[Callable] = None
    session_started: Optional[Callable] = None
    session_stopped: Optional[Callable] = None

class AzureSpeechService:
    active_speech_recognizers = {}

    client_id_to_session_id = {}
    session_id_to_client_id = {}

    api_key = os.getenv("AZURE_COGNITIVE_SERVICES_API_KEY_1")
    service_region = os.getenv("AZURE_COGNITIVE_SERVICES_REIGON")
    speech_config = SpeechConfig(subscription=api_key, region=service_region)

    speech_sdk = azure_speechsdk
    firebase_storage = FirebaseStorage()

    def recognize_speech_from_file(self, file_path: str) -> str:
        audio_config = AudioConfig(filename=file_path)
        speech_recognizer = SpeechRecognizer(
            speech_config=AzureSpeechService.speech_config, audio_config=audio_config
        )

        result = speech_recognizer.recognize_once_async().get()
        return result.text

    def recognize_speech_from_stream(self, stream: bytes) -> str:
        audio_config = AudioConfig(
            stream=PullAudioInputStream(stream)
        )
        speech_recognizer = SpeechRecognizer(
            speech_config=AzureSpeechService.speech_config, audio_config=audio_config
        )

        result = speech_recognizer.recognize_once_async().get()
        return result.text

    def recognize_speech_from_url(self, url: str) -> str:
        audio_config = AudioConfig(
            stream=PullAudioInputStream.create_from_uri(url)
        )
        speech_recognizer = SpeechRecognizer(
            speech_config=AzureSpeechService.speech_config, audio_config=audio_config
        )

        result = speech_recognizer.recognize_once_async().get()
        return result.text

    def recognize_speech_from_microphone(self) -> str:
        audio_config = AudioConfig(
            stream=PullAudioInputStream.create_microphone_input()
        )
        speech_recognizer = SpeechRecognizer(
            speech_config=AzureSpeechService.speech_config, audio_config=audio_config
        )

        result = speech_recognizer.recognize_once_async().get()
        return result.text

    def recognize_speech_from_microphone_continuous(self) -> str:
        audio_config = AudioConfig(
            stream=PullAudioInputStream.create_microphone_input()
        )
        speech_recognizer = AzureSpeechService.get_speech_recognizer(
            audio_config)

        done = False

        def stop_cb(evt):
            print('CLOSING on {}'.format(evt))
            speech_recognizer.stop_continuous_recognition()
            nonlocal done
            done = True

        all_results = []

        def recognized_cb(evt):
            print('RECOGNIZED: {}'.format(evt))
            all_results.append(evt.result.text)

        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition()
        while not done:
            time.sleep(.5)

        return all_results

    def synthesize_speech_from_text(self, text, stream: bool = False) -> bytes:
        speech_synthesizer = self.speech_sdk.SpeechSynthesizer(
            speech_config=AzureSpeechService.speech_config
        )
        result = speech_synthesizer.speak_text_async(text).get()
        if stream:
            return result.audio_data
        return result.audio_data.getvalue()

    def _default_viseme_callback(self, evt):
        print("Viseme event received: audio offset: {}ms, viseme id: {}.".format(
            evt.audio_offset / 10000, evt.viseme_id))
        # `Animation` is an xml string for SVG or a json string for blend shapes
        animation = evt.animation

    def _get_synthesizer_stream(self, synthesize: SpeechSynthesisResult):
        return synthesize.audio_data
    
    @staticmethod
    def load_azure_ssml_cfg():
        ssml_path = os.path.join(os.path.dirname(__file__), "cfg", "azure_ssml_cfg.json")

        with open(ssml_path, "r") as f:
            return json.load(f)
        
    @staticmethod
    def load_azure_viseme_cfg():
        viseme_path = os.path.join(os.path.dirname(__file__), "cfg", "azure_viseme_cfg.json")
        with open(viseme_path, 'r') as f:
            return json.load(f)
        
    @staticmethod
    def format_viseme_result(viseme_result, viseme_cfg = None):
        if viseme_cfg is None:
            viseme_cfg = AzureSpeechService.load_azure_viseme_cfg()

        audio_offset = viseme_result.audio_offset
        viseme_id = viseme_result.viseme_id
        animation = viseme_result.animation

        if animation == '':
            return {
                'AudioOffset': audio_offset,
                'VisemeId': viseme_id,
                'Animation': animation
            }
        
        animation = json.loads(animation)

        fps = 60
        timestep = 1 / fps
        blend_data = []





    @staticmethod
    def text_to_ssml(text):
        # Replace special characters with HTML Ampersand Character Codes
        # These Codes prevent the API from confusing text with
        # SSML commands
        # For example, '<' --> '&lt;' and '&' --> '&amp;'
        ssml_cfg = AzureSpeechService.load_azure_ssml_cfg()['tags']
        root_tags = ssml_cfg['root_tags']

        xml_document = XMLDoc()

        xml_tags = []
        for tag in root_tags:
            voice_args = {
                "voice": {
                    "text": text
                }
            }

            xml_tag = XMLTag.cfg_tag_to_xml_tag(xml_document.document, ssml_cfg, tag, ssml_cfg[tag], voice_args)
            xml_tags.append(xml_tag)

        for xml_tag in xml_tags:
            xml_document.document.appendChild(xml_tag.element)

        
        return xml_document
    
    @staticmethod
    def save_audio_to_file(storage_bucket: str, file_name: str, audio: bytes):
        audio_stream = io.BytesIO(audio)
        audio_stream.seek(0)

        result = FirebaseStorage.upload_file_from_bytes(
            storage_bucket=storage_bucket,
            file_name=file_name,
            file_bytes=audio_stream
        )

        print(result)

        return result
    
    @staticmethod
    def assign_recognition_callbacks(speech_recognizer, recognition_callbacks: AzureRecognitionCallbacks):
        recognizing = recognition_callbacks.recognizing
        recognized = recognition_callbacks.recognized
        canceled = recognition_callbacks.canceled
        session_started = recognition_callbacks.session_started
        session_stopped = recognition_callbacks.session_stopped

        if recognizing is not None:
            speech_recognizer.recognizing.connect(recognizing)
        if recognized is not None:
            speech_recognizer.recognized.connect(recognized)
        if canceled is not None:
            speech_recognizer.canceled.connect(canceled)
        if session_started is not None:
            speech_recognizer.session_started.connect(session_started)
        if session_stopped is not None:
            speech_recognizer.session_stopped.connect(session_stopped)

    @staticmethod
    def track_client_and_session(client_id: str, session_id: str):
        AzureSpeechService.client_id_to_session_id[client_id] = session_id
        AzureSpeechService.session_id_to_client_id[session_id] = client_id

    @staticmethod
    def remove_client_and_session(client_id: str, session_id: str):
        if AzureSpeechService.client_id_to_session_id.get(client_id, None) is None or \
        AzureSpeechService.session_id_to_client_id.get(session_id, None) is None:
            return

        del AzureSpeechService.client_id_to_session_id[client_id]
        del AzureSpeechService.session_id_to_client_id[session_id]
    
    def recognize_text_from_audio_stream(
            self, 
            audio_queue: queue.Queue, 
            client_id: str, 
            recognition_callbacks: AzureRecognitionCallbacks,
            kill_event: asyncio.Event
        ):
        stream = PushAudioInputStream()
        audio_config = AudioConfig(stream=stream)
        speech_recognizer = SpeechRecognizer(
            speech_config=AzureSpeechService.speech_config, audio_config=audio_config
        )

        AzureSpeechService.assign_recognition_callbacks(speech_recognizer, recognition_callbacks)
        # speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt.result.text)))
        # speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt.result.text)))
        # speech_recognizer.canceled.connect(lambda evt: print('CANCELED: {}'.format(evt.result.text)))
        # speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt.result.text)))
        # speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt.result.text)))

        session_id = speech_recognizer.properties.get_property(PropertyId.Speech_SessionId)

        AzureSpeechService.client_id_to_session_id[client_id] = session_id
        AzureSpeechService.session_id_to_client_id[session_id] = client_id

        speech_recognizer.start_continuous_recognition_async()

        while True:
            if kill_event.is_set():
                break

            stop = False
            if stop:
                break

            while not audio_queue.empty():
                audio = audio_queue.get(block=False)
                if audio is None:
                    stop = True
                    break

                stream.write(audio)

        stream.close()
        speech_recognizer.stop_continuous_recognition_async()

    def synthesize_speech_with_viseme(self, text, viseme_callback=None, stream=True):
        speech_synthesizer = SpeechSynthesizer(
            speech_config=AzureSpeechService.speech_config,
            audio_config=None
        )

        # Connect callbacks to the events fired by the speech synthesizer
        if viseme_callback is None:
            viseme_callback = self._default_viseme_callback

        speech_synthesizer.viseme_received.connect(viseme_callback)

        # Convert text to ssml
        ssml = AzureSpeechService.text_to_ssml(text)

        result = speech_synthesizer.speak_ssml_async(str(ssml)).get()

        if result.reason == ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized to speaker for text [{}]".format(text))

        elif result.reason == ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))

            if cancellation_details.reason == CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))

        return result

# if __name__ == '__main__':
#     az_service = AzureSpeechService()
    
#     result = az_service.synthesize_speech_with_viseme("The rainbow has seven colors.")
#     print(result.audio_data.getvalue())
