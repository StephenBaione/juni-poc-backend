from fastapi import WebSocket

from typing import List

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        # self.speech_recognition_service = SpeechRecognitionService(self.speech_buffer)
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket, client_id=None) -> None:
        self.active_connections.remove(websocket)

        try:
            await websocket.close()
        except Exception as e:
            print('disconnect', e)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(message)