from fastapi import APIRouter, Depends, Response, status, WebSocket, Body
from fastapi.responses import StreamingResponse

from starlette.websockets import WebSocketState, WebSocketDisconnect

from internal.handlers.azure_speech_handlers import AzureSpeechHandler

from internal.services.socket_service import ConnectionManager

import asyncio

from typing import Optional

azure_speech_handler = AzureSpeechHandler()
azure_speech_router = APIRouter(prefix='/speech', tags=['Azure Speech'])

connection_manager = ConnectionManager()

from uuid import uuid4
import json

from urllib.parse import unquote

@azure_speech_router.post('/viseme')
async def viseme(response: Response, text: str = Body(...)):
    request_id = str(uuid4())

    text = json.loads(text)['text']
    text = unquote(text)
    print(text)

    response.status_code = status.HTTP_200_OK
    result = azure_speech_handler.handle_post_viseme_request(text, request_id)

    if result is None:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'message': 'Internal Server Error'}
    
    return result

@azure_speech_router.websocket('/viseme/stream')
async def viseme_stream(websocket: WebSocket, request_id: int):
    await ConnectionManager.connect(websocket)

    kill_event = asyncio.Event()

@azure_speech_router.websocket('/stt/transcribe')
async def stt_trackscribe(websocket: WebSocket):
    try:
        await azure_speech_handler.handle_transribe_stream_request(websocket)
        await connection_manager.disconnect(websocket)

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)

    except Exception as e:
        print(e)