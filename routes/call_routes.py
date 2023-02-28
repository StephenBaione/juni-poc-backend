import os
from dotenv import load_dotenv
load_dotenv()

import threading
import asyncio

from internal.services.socket_service_bridge import SpeechClientBridge
import base64

import queue

from internal.services.openai_service import OpenAIClient
openai_client = OpenAIClient()

from internal.services.text_to_speech_service import TextToSpeechService

from internal.request_models.call_requests import CallRequest

from fastapi import APIRouter, Response, Depends, Request, WebSocket
from fastapi.responses import StreamingResponse
from starlette.websockets import WebSocketState

from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Gather, Redirect, Start

call_router = APIRouter(prefix='/call', tags=['Call'])

@call_router.get('/demo')
@call_router.post('/demo')
async def demo():
    resp = VoiceResponse()
    # resp.say('Hello World. I am now recording.', voice='alice')
    connect = Connect()
    ngrok_endpoint = os.getenv('NGROK_ENDPOINT')
    ngrok_endpoint = ngrok_endpoint.replace('https', 'wss')

    ngrok_endpoint += '/call/ws/1234'

    connect.stream(url=ngrok_endpoint)
    resp.append(connect)

    return Response(content=str(resp), media_type='application/xml')

@call_router.get('/recieve')
@call_router.post('/recieve')
async def demo2(respone: Response, call_request = Depends(CallRequest)):
    print('receiving', call_request)
    ngrok_endpoint = os.getenv('NGROK_ENDPOINT')
    ngrok_endpoint = ngrok_endpoint.replace('https', 'ws')

    ngrok_endpoint += '/audio/ws/1234'

    resp = VoiceResponse()
    if not call_request.initiated_conversation:
        resp.say('Hello World. Keep on rocking in the free world.', voice='alice')
        call_request.history += 'Hello World. Keep on rocking in the free world.'
        call_request.initiated_conversation = True

    chat_message_as_params = call_request.to_param_string()
    print(chat_message_as_params)
    gather = Gather(input='speech', action=f'/call/respond?{chat_message_as_params}', speech_timeout='auto', speech_model='phone_call')
    resp.append(gather)

    return Response(content=str(resp), media_type='application/xml')

@call_router.get('/respond')
@call_router.post('/respond')
async def response(request: Request, respone: Response, call_request = Depends(CallRequest)):
    print('responding', call_request)
    resp = VoiceResponse()
    print(request)

    history = call_request.history
    print(history)
    completion = openai_client.create_completion('text-davinci-002', 'Tell me something interesting')
    chat_message = OpenAIClient.decode_completion_to_chat_message(completion, 'text-davinci-002')
    message = chat_message.message
    print(message)
    resp.say(message, voice='alice')

    ngrok_endpoint = os.getenv('NGROK_ENDPOINT')
    ngrok_endpoint += '/call/recieve'
    resp.redirect(ngrok_endpoint, method='POST')

    return Response(content=str(resp), media_type='application/xml')

def on_transcription_response(response, decode_queue: queue.Queue):
    if not response.results:
        return

    result = response.results[0]
    if not result.alternatives:
        return

    if result.is_final:
        transcription = result.alternatives[0].transcript
        decode_queue.put(transcription, block=False)
    else:
        decode_queue.put('||TALKING||', block=False)

async def receive_audio(websocket: WebSocket, speech_client_bridge: SpeechClientBridge):
    while True:
        print('listening')
        
        message = await websocket.receive()
        print(message)
        if message.get('type', '') == 'websocket.connect':
            continue
        if message is None:
            speech_client_bridge.add_request(None)
            speech_client_bridge.terminate()
            break

        speech_client_bridge.add_request(message)

async def send_audio_loop(websocket: WebSocket, _buffer: queue.Queue):
    while True:
        if not _buffer.empty():
            audio = _buffer.get()
            if audio is None:
                break
            
            await websocket.send_text(audio)

def send_audio(websocket, _buffer):
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_audio_loop(websocket, _buffer))
    
def start_speech_client_bridge(websocket, _buffer):
    speech_client_bridge = SpeechClientBridge(on_transcription_response, _buffer)
    thread = threading.Thread(target=speech_client_bridge.start)
    thread.start()
    return speech_client_bridge

async def listen_loop(websocket: WebSocket, speech_client_bridge: SpeechClientBridge, decode_queue: queue.Queue):
    import time

    last_decode = time.time()
    transcription = ''
    while True:
        try:
            message = await websocket.receive_json()
            if message.get('type', '') == 'websocket.connect':
                continue
            elif message.get('event', '') == 'connected':
                continue
            elif message.get('event', '') == 'start':
                speech_client_bridge.stream_sid = message['streamSid']
                continue
            if message is None:
                speech_client_bridge.add_request(None)
                speech_client_bridge.terminate()
                break

            elif message.get('event', '') == 'media':
                media = message["media"]
                chunk = base64.b64decode(media["payload"])
                speech_client_bridge.add_request(chunk)

            # Check decode queue for transcription updates
            if not decode_queue.empty():
                last_decode = time.time()
                last_transcription = decode_queue.get()
                if last_transcription == '||TALKING||':
                    continue

                transcription += last_transcription
                print(transcription)

            if time.time() - last_decode > 3:
                speech_client_bridge.terminate()
                break

        except Exception as e:
            print(e)
            break

@call_router.websocket('/ws/{conversation_id}')
async def websocket_endpoint(websocket: WebSocket, conversation_id):
    await websocket.accept()

    decode_queue = queue.Queue()

    speech_client_bridge = start_speech_client_bridge(websocket, decode_queue)

    import time

    last_decode = time.time()
    transcription = ''
    while True:
        try:
            message = await websocket.receive_json()
            if message.get('type', '') == 'websocket.connect':
                continue
            elif message.get('event', '') == 'connected':
                continue
            elif message.get('event', '') == 'start':
                speech_client_bridge.stream_sid = message['streamSid']
                continue
            if message is None:
                speech_client_bridge.add_request(None)
                speech_client_bridge.terminate()
                break

            elif message.get('event', '') == 'media':
                media = message["media"]
                chunk = base64.b64decode(media["payload"])
                speech_client_bridge.add_request(chunk)

            # Check decode queue for transcription updates
            if not decode_queue.empty():
                last_decode = time.time()
                last_transcription = decode_queue.get()
                if last_transcription == '||TALKING||':
                    continue

                transcription += last_transcription
                print(transcription)

            if time.time() - last_decode > 3:
                speech_client_bridge.terminate()
                break

        except Exception as e:
            print(e)
            break

    # Make sure decode queue is empty
    while not decode_queue.empty():
        last_transcription = decode_queue.get(block=False)
        if last_transcription == '||TALKING||':
            continue

        transcription += last_transcription

    text_to_speech_service = TextToSpeechService()
    completion = openai_client.create_completion('text-davinci-002', transcription)
    chat_message = OpenAIClient.decode_completion_to_chat_message(completion, 'text-davinci-002')
    message = chat_message.message
    print(message)
    socket_message = {
        'event': 'media',
        'streamSid': speech_client_bridge.stream_sid,
        'media': {
            'payload': '',
        }
    }

    import json
    audio = text_to_speech_service.talk(message)
    # payload = base64.b64encode(audio).decode('utf-8')
    # socket_message['media']['payload'] = payload
    # await websocket.send_text(json.dumps(socket_message))

    # Skip header bytes
    audio = audio[56:]
    # payload = base64.b64encode(audio).decode('ascii')
    # socket_message['media']['payload'] = payload
    # print('sending', len(payload))
    # await websocket.send_text(json.dumps(socket_message))


    # _buffer = queue.Queue()
    # send_thread = threading.Thread(target=send_audio, args=(websocket, _buffer))
    # send_thread.start()

    print('parsing')
    chunk_length = 512
    for i in range(0, len(audio), 512):
        if i + 512 > len(audio):
            payload = base64.b64encode(audio[i:]).decode('ascii')
            socket_message = {
                'event': 'media',
                'streamSid': speech_client_bridge.stream_sid,
                'media': {
                    'payload': payload,
                }
            }
            await websocket.send_text(json.dumps(socket_message))

        payload = base64.b64encode(audio[i:i+512]).decode('ascii')
        socket_message = {
            'event': 'media',
            'streamSid': speech_client_bridge.stream_sid,
            'media': {
                'payload': payload,
            }
        }
        await websocket.send_text(json.dumps(socket_message))

    print('done parsing')
    # _buffer.put(None)

    # while not _buffer.empty():
    #     await asyncio.sleep(0.1)

    speech_client_bridge.terminate()
    await websocket.close()
