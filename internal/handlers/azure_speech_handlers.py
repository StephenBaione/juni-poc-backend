from ..services.azure_speech_service import AzureSpeechService, AzureRecognitionCallbacks, ResultReason, PropertyId, SpeechRecognitionEventArgs, SessionEventArgs

from data.firebase.result_objects.storage_results import FileOperationResult

from starlette.websockets import WebSocketDisconnect

from fastapi import WebSocket

import json

import asyncio
import queue

from typing import Any

from internal.services.socket_service import SocketService, LoopCallBacks, MessageTypes

from pydantic import BaseModel

from enum import Enum

class SendQueueEvents(BaseModel):
    client_id: str
    event: str
    data: dict


class SendQueueTypes(Enum):
    TRANSCRIBE_STREAM_STARTED = 'TRANSCRIBE_STREAM_STARTED'
    TRANSCRIBE_STREAM_STOPPED = 'TRANSCRIBE_STREAM_STOPPED'
    TRANSCRIBE_STREAM_RECOGNIZED = 'TRANSCRIBE_STREAM_RECOGNIZED'
    TRANSCRIBE_STREAM_RECOGNIZING = 'TRANSCRIBE_STREAM_RECOGNIZING'


class AzureSpeechHandler:
    viseme_cfg = AzureSpeechService.load_azure_viseme_cfg()
    viseme_index_map = viseme_cfg['VisemeIndexMap']

    viseme_frames_per_second = viseme_cfg['FramesPerSecond']

    socket_service = SocketService()

    static_send_queues = {}
    client_kill_events = {}

    client_final_indexes = {}

    def __init__(self) -> None:
        self.azure_speech_service = AzureSpeechService()
        self.viseme_queue = queue.Queue()
        self.websocket = None

    # STATIC METHODS
    @staticmethod
    def map_blend_shapes_to_shape_keys(frame_index: int, blend_shapes: dict) -> dict:
        """Map raw blend shape data to shape keys

        Args:
            frame_index (int): Indicated the number of frames preceeding first frame in this group
            blend_shapes (list(list)): List of blend shape data,
                where each blend shape is a list, where
                index correlates to shape key
                and value correlates to shape key value AT THIS TIME STEP

        Returns:
            list(dict): List with the following items:
                animation = 
                {
                    'time': time,
                    'animation_group': [
                        {
                            'shape_key': shape_key,
                            'value': value
                        }
                    ]
                }
        """
        viseme_index_map = AzureSpeechHandler.viseme_index_map

        animations = []

        # Calculate starting time step based on frame index and fps
        time_step = 1 / AzureSpeechHandler.viseme_frames_per_second
        time = frame_index * time_step

        for blend_shape in blend_shapes:
            animation = {
                'time': time,
                'animation_group': []
            }

            animation_group = []
            for index, value in enumerate(blend_shape):
                shape_key = viseme_index_map[str(index)]
                animation_item = {
                    'shape_key': shape_key,
                    'value': value
                }

                animation_group.append(animation_item)

            animation['animation_group'] = animation_group
            animations.append(animation)
            time += time_step

        return animations
    
    @staticmethod
    def set_client_kill_event(client_id: str):
        AzureSpeechHandler.client_kill_events[client_id] = asyncio.Event()

    @staticmethod
    def get_client_kill_event(client_id: str):
        return AzureSpeechHandler.client_kill_events[client_id]
    
    @staticmethod
    def terminate_client_event(client_id: str):
        if client_id not in AzureSpeechHandler.client_kill_events.keys():
            return

        AzureSpeechHandler.client_kill_events[client_id].set()

    # Text to Speech
    async def handle_text_to_speech_post(self, text: str) -> FileOperationResult:
        result = self.azure_speech_service.synthesize_speech_from_text(text)
        return result
    
    # VISEME STREAM
    async def handle_websocket_viseme_stream(self, websocket: WebSocket):
        await SocketService.add_client(websocket)

        receive_loop_events, send_loop_events = SocketService.get_loop_events(
            websocket)

        receive_queue, send_queue = SocketService.get_bidirectional_queues(
            websocket)

        await SocketService.start_loop(
            websocket,
            receive_queue=receive_queue,
            send_queue=send_queue,
            receive_loop_events=receive_loop_events,
            send_loop_events=send_loop_events
        )

        await self.send_viseme_loop()

    def _viseme_stream_callback(self, viseme_event: dict):
        audio_offset = viseme_event.audio_offset / 1000
        viseme_id = viseme_event.viseme_id
        animation = viseme_event.animation

        if animation == '':
            return

        animation_data = json.loads(animation)

        frame_index = animation_data.get('FrameIndex', None)
        blend_shapes = animation_data.get('BlendShapes', None)

        animations = AzureSpeechHandler.map_blend_shapes_to_shape_keys(
            frame_index,
            blend_shapes
        )

        viseme = {
            "audio_offset": audio_offset,
            "viseme_id": viseme_id,
            "animation": animations
        }

        self.viseme_queue.put(viseme)

    async def send_viseme_loop(self):
        websocket = self.websocket
        viseme_queue = self.viseme_queue

        while not self.kill_event.is_set():
            viseme = viseme_queue.get()

            if not viseme_queue.empty():
                viseme = viseme_queue.get(block=False)
                await websocket.send_json(viseme)

    # VISEME REQUEST
    def handle_post_viseme_request(self, text: str, request_id: str) -> dict:
        try:
            result = \
                self.azure_speech_service \
                .synthesize_speech_with_viseme(
                    text,
                    viseme_callback=self._viseme_stream_callback
                )
            audio = result.audio_data

            # Save Audio to firestore storage
            result: FileOperationResult = AzureSpeechService.save_audio_to_file(
                storage_bucket='cogntive-services-tts',
                file_name=f'{request_id}.wav',
                audio=audio
            )

            visemes = []
            while not self.viseme_queue.empty():
                viseme = self.viseme_queue.get(block=False)
                visemes.append(viseme)

            return {
                "FileResult": result,
                "Visemes": visemes,
                "Exception": None
            }
        except Exception as e:
            print(e)
            return {
                "FileResult": None,
                "Visemes": None,
                "Exception": f"{e}"
            }

    def handle_speech_synthesis_viseme_request(
        self,
        text: str,
    ) -> dict:

        try:
            async_event_loop = asyncio.get_event_loop()
            send_viseme_task = async_event_loop.create_task(
                self.send_viseme_loop())

            async_event_loop.run_until_complete(send_viseme_task)

            self.azure_speech_service.synthesize_speech_with_viseme(text, viseme_callback=self._viseme_stream_callback)

        except Exception as e:
            print(e)
            return None
  
    # TRANSCRIBE STREAM CALLBACKS
    def stream_cancelled_callback(self, event: dict):
        print(event)

    def stream_session_started_callback(self, event: SessionEventArgs):
        print(event)

    def stream_session_ended_callback(self, event: SessionEventArgs):
        print(event)

    def stream_recognizing_callback(self, event: SpeechRecognitionEventArgs):
        try:
            if event.result.reason == ResultReason.RecognizingSpeech:
                session_id = event.session_id
                client_id = AzureSpeechService.session_id_to_client_id[session_id]

                send_queue: queue.Queue = AzureSpeechHandler.static_send_queues[client_id]

                send_queue_event = SendQueueEvents(
                    client_id=client_id,
                    event=SendQueueTypes.TRANSCRIBE_STREAM_RECOGNIZING.value,
                    data={
                        'text': event.result.text,
                    }
                )

                send_queue.put(send_queue_event, block=False)

        except Exception as e:
            print(e)

    def stream_recognized_callback(self, event: SpeechRecognitionEventArgs):
        try:
            if event.result.reason == ResultReason.RecognizedSpeech:
                session_id = event.session_id
                client_id = AzureSpeechService.session_id_to_client_id[session_id]


                data= {
                    'text': event.result.text,
                }

                self._send_data_to_client(client_id, SendQueueTypes.TRANSCRIBE_STREAM_RECOGNIZED, data)
        except Exception as e:
            print('RECOGNIZED ERROR', e)
    
    def _stream_transcribe_afer_queue_op_send(self, event: SendQueueEvents):
        return dict(event)
    
    
    def _send_data_to_client(self, client_id: str, event: SendQueueTypes, data: dict):
        try:
            send_queue = AzureSpeechHandler.static_send_queues[client_id]
            send_queue_event = SendQueueEvents(
                client_id=client_id,
                event=event.value,
                data=data
            )

            send_queue.put(send_queue_event, block=False)
        except Exception as e:
            print(e)
            print('recognized', e)

    async def handle_transribe_stream_request(self, websocket: WebSocket):
        try:
            client_id = await SocketService.add_client(websocket)

            # Get events and queues
            receive_loop_events, send_loop_events = SocketService.get_loop_events()
            receive_queue, send_queue = SocketService.get_bidirectional_queues()

            # Add send queue to static send queues
            AzureSpeechHandler.static_send_queues[client_id] = send_queue

            # Set recognition callbacks for trascripting
            azure_recognition_callback = AzureRecognitionCallbacks(
                recognizing=self.stream_recognizing_callback,
                recognized=self.stream_recognized_callback,
                canceled=self.stream_cancelled_callback,
                session_started=self.stream_session_started_callback,
                session_stopped=self.stream_session_ended_callback,
            )

            # Set callbacks for send loop
            send_callbacks = LoopCallBacks(
                after_queue_op=self._stream_transcribe_afer_queue_op_send
            )

            # Start recognition thread
            import threading
            recognition_thread = threading.Thread(
                target=self.azure_speech_service.recognize_text_from_audio_stream,
                args=(receive_queue, client_id, azure_recognition_callback, receive_loop_events.kill_event)
            )
            recognition_thread.start()

            # Start listen loop
            listen_loop = asyncio.create_task(SocketService.start_listen_loop(
                websocket,
                receive_loop_events,
                receive_queue
            )
            )

            # Start send loop
            send_loop = asyncio.create_task(SocketService.start_send_loop(
                    websocket,
                    send_loop_events,
                    send_queue,
                    MessageTypes.JSON,
                    send_callbacks,
                )
            )

            await asyncio.gather(listen_loop, send_loop)
            recognition_thread.join()

        except WebSocketDisconnect:
            print('disconnected')
            AzureSpeechHandler.terminate_client_event(client_id)
            raise WebSocketDisconnect

        except Exception as e:
            print(e)
            send_loop_events.kill_event.set()
