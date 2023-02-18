from fastapi import WebSocket, WebSocketDisconnect, WebSocketException

from typing import List, Dict

from six.moves import queue

class WebSocketClient:
    def __init__(
        self,
        thread = None,
        conn = None
    ) -> None:
        self.client_id = None
        self.is_connected = False

        self._buffer = queue.Queue()
        self._thread = thread
        self._conn = conn

        self._listeners: List[WebSocketClient] = []

    def set_websocket(self, websocket: WebSocket, is_connected = False):
        self.websocket = websocket

        # Check if websocket is connected
        self.is_connected = is_connected

    async def connect(self, websocket: WebSocket, client_id: int) -> None:
        self.client_id = client_id
        self.websocket = websocket
        await self.websocket.accept()
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

        if self._buffer is not None:
            self._buffer.put(None)

        if self._thread is not None:
            self._thread.join()

        self.websocket.close()

    def start_thread(self):
        self.is_connected = True
        self._thread.start()
        print('Thread started')

    async def send_message(self, message: str) -> None:
        await self.websocket.send_text(message)

    def write_to_buffer(self, data: bytes) -> None:
        self._buffer.put(data)

    def read_from_buffer(self, block=True, timeout=None) -> bytes:
        if self._buffer.empty():
            return None

        if timeout is not None:
            return self._buffer.get(block, timeout=timeout)

        return self._buffer.get(block)

    async def receive_message(self) -> str:
        try:
            data = await self.websocket.receive_text()
            return data
        except WebSocketDisconnect:
            self.disconnect()
            return None
        except WebSocketException:
            self.disconnect()
            return None

    def generator(self):
        while not self.is_connected:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            print(len(self._buffer.queue))
            chunk = self._buffer.get()
            if chunk is None:
                return
            data = [chunk]


            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buffer.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield bytes("".join(data), 'utf-8')

    def add_listener(self, listener):
        self._listeners.append(listener)

    def remove_listener(self, listener):
        self._listeners.remove(listener)

    def notify_listeners(self, message):
        print('notify_listeners', message)
        for listener in self._listeners:
            listener.write_to_buffer(message)

class WebSocketClientManager:
    def __init__(self) -> None:
        self.clients: List[WebSocketClient] = []

    async def connect(self, websocket: WebSocket, client_id: int) -> None:
        client = WebSocketClient()
        await client.connect(websocket, client_id)
        self.clients.append(client)

    def disconnect(self, client_id: int) -> None:
        client = self.get_client(client_id, None)
        if client is None:
            return False

        client.disconnect()
        return True

    def disconnect_all(self) -> None:
        for client in self.clients:
            client.disconnect()

    def get_client(self, client_id: int) -> WebSocketClient:
        for client in self.clients:
            if client.client_id == client_id:
                return client

        return None

    async def send_message_to_client(self, message: str, client_id: int) -> None:
        client = self.get_client(client_id)
        if client is not None:
            await client.send_message(message)

    async def broadcast(self, message: str) -> None:
        for client in self.clients:
            await client.send_message(message)

