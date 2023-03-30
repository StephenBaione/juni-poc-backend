from typing import List, Any, Callable, Optional, Tuple, Union

from pydantic import BaseModel

from fastapi import WebSocket

from uuid import uuid4

import queue

from enum import Enum

import asyncio

class MessageTypes(Enum):
    TEXT = 'text'
    JSON = 'json'
    BINARY = 'binary'

class ConnectionManager:
    clients = {}

    @staticmethod
    async def connect(websocket: WebSocket, client_id) -> bool:
        try:
            await websocket.accept()
            
            if ConnectionManager.get_client(client_id) is None:
                ConnectionManager.clients[client_id] = websocket

            return True

        except Exception as e:
            print('connect', e)
            return False

    @staticmethod
    def get_client(client_id) -> WebSocket:
        return ConnectionManager.clients.get(client_id, None)

    @staticmethod
    async def disconnect(websocket: WebSocket, client_id=None) -> bool:
        try:
            await websocket.close()
            return True

        except Exception as e:
            print('disconnect', e)
            return False
        
    @staticmethod
    async def disconnect_all() -> bool:
        try:
            for _, client in ConnectionManager.clients.items():
                await ConnectionManager.disconnect(client)

            return True
        
        except Exception as e:
            print('disconnect_all', e)
            return False

    @staticmethod
    async def send_message(client: Union[WebSocket, str], message_type: MessageTypes, data: Any) -> bool:
        try:
            if isinstance(client, str):
                client = ConnectionManager.get_client(client)

            if message_type == MessageTypes.TEXT:
                await client.send_text(data)
            elif message_type == MessageTypes.JSON:
                await client.send_json(data)
            elif message_type == MessageTypes.BINARY:
                await client.send_bytes(data)

            return True
        except Exception as e:
            print('send_message', e)

            return False

    @staticmethod
    async def broadcast(message_type: MessageTypes, data) -> bool:
        try:
            for _, client in ConnectionManager.clients.items():
                await ConnectionManager.send_message(client, message_type, data)

            return True

        except Exception as e:
            print('broadcast', e)
            return False

class LoopEvents(BaseModel):
    kill_event: Any
    run_event: Any

class LoopCallBacks(BaseModel):
    before_socket_op: Optional[Callable] = None
    after_socket_op: Optional[Callable] = None

    before_queue_op: Optional[Callable] = None
    after_queue_op: Optional[Callable] = None

class SocketService:
    connection_manager: ConnectionManager = ConnectionManager()

    @staticmethod
    async def add_client(websocket: WebSocket) -> str:
        client_id = str(uuid4())

        if await SocketService.connection_manager.connect(websocket, client_id):
            return client_id
        
        return None

    @staticmethod
    def remove_client(client_id: str) -> bool:
        client = SocketService.connection_manager.get_client(client_id)
        if client is not None:
            return SocketService.connection_manager.disconnect(client, client_id)
        
        return False
    
    # TODO: Find way to automate hooks
    @staticmethod
    async def start_listen_loop(
        websocket: WebSocket,
        loop_events: LoopEvents,
        queue: queue.Queue,
        callbacks: LoopCallBacks = None):

        before_socket_op = callbacks.before_socket_op if callbacks is not None else None
        after_socket_op = callbacks.after_socket_op if callbacks is not None else None

        before_queue_op = callbacks.before_queue_op if callbacks is not None else None
        after_queue_op = callbacks.after_queue_op if callbacks is not None else None

        kill_event: asyncio.Event = loop_events.kill_event
        run_event: asyncio.Event = loop_events.run_event

        while not kill_event.is_set():
            while not run_event.is_set():
                if kill_event.is_set():
                    break

                try:
                    if before_socket_op is not None:
                        before_socket_op()

                    try:
                        data = await websocket.receive_bytes()

                    except Exception as e:
                        print('start_listen_loop', e)
                        run_event.set()
                        kill_event.set()

                    if after_socket_op is not None:
                        after_socket_op()

                    if before_queue_op is not None:
                        before_queue_op()
                    
                    queue.put(data, block=False)

                    if after_queue_op is not None:
                        after_queue_op()
                except Exception as e:
                    print('get_data_loop', e)
                    break

    @staticmethod
    async def start_send_loop(
        websocket: WebSocket,
        loop_events: LoopEvents,
        queue: queue.Queue,
        message_type: MessageTypes,
        callbacks: LoopCallBacks = None,
        sendMessageEvent: Optional[asyncio.Event] = None):

        kill_event = loop_events.kill_event
        run_event = loop_events.run_event

        before_socket_op = callbacks.before_socket_op if callbacks is not None else None
        after_socket_op = callbacks.after_socket_op if callbacks is not None else None

        before_queue_op = callbacks.before_queue_op if callbacks is not None else None
        after_queue_op = callbacks.after_queue_op if callbacks is not None else None

        while not kill_event.is_set():
            while not run_event.is_set():
                try:
                    if kill_event.is_set():
                        break

                    if not queue.empty():

                        if before_queue_op is not None:
                            before_queue_op()

                        data = queue.get(block=False)

                        if after_queue_op is not None:
                            data = after_queue_op(data)

                        if before_socket_op is not None:
                            before_socket_op()

                        try:
                            await SocketService.connection_manager.send_message(
                                websocket,
                                message_type,
                                data
                            )
                        
                        except Exception as e:
                            run_event.set()
                            kill_event.set()

                        if after_socket_op is not None:
                            after_socket_op()

                    await asyncio.sleep(0.02)
                except Exception as e:
                    print('send_data_loop', e)
                    break

    @staticmethod
    async def stop_loop(
        receive_loop_events: LoopEvents,
        send_loop_events: LoopEvents):

        try:
            # Both share the same kill event
            receive_loop_events.kill_event.set()

            # Stop both run events
            receive_loop_events.run_event.set()
            send_loop_events.run_event.set()

        except Exception as e:
            print('stop_loop', e)

    @staticmethod
    async def start_loop(
        websocket,
        receive_queue: queue.Queue,
        send_queue: queue.Queue,
        receive_loop_events: LoopEvents,
        send_loop_events: LoopEvents,
        receive_callbacks: LoopCallBacks = None,
        send_callbacks: LoopCallBacks = None):

        try:
            receive_loop = asyncio.create_task(
                SocketService.start_listen_loop(
                    websocket,
                    receive_loop_events,
                    receive_queue,
                    receive_callbacks))
            
            send_loop = asyncio.create_task(
                SocketService.start_send_loop(
                    websocket,
                    send_loop_events,
                    send_queue,
                    send_callbacks))
            
            await asyncio.gather(receive_loop, send_loop)

        except Exception as e:
            print('start_loop', e)

    @staticmethod
    def get_loop_events() -> LoopEvents:
        kill_event = asyncio.Event()
        receive_run_event = asyncio.Event()
        send_run_event = asyncio.Event()

        send_loop_events = LoopEvents(
            kill_event=kill_event,
            run_event=send_run_event
        )

        receive_loop_events = LoopEvents(
            kill_event=kill_event,
            run_event=receive_run_event
        )

        return receive_loop_events, send_loop_events
    
    @staticmethod
    def get_bidirectional_queues() -> Tuple[queue.Queue, queue.Queue]:
        receive_queue = queue.Queue()
        send_queue = queue.Queue()

        return receive_queue, send_queue
    
    @staticmethod
    def get_one_directional_queue() -> queue.Queue:
        return queue.Queue()





