import queue
from fastapi import WebSocket
import asyncio

from abc import ABC, abstractmethod

class ClientServiceBridge(ABC):
    def __init__(self, rcv_queue: queue.Queue, result_queue: queue.Queue, websocket: WebSocket, service) -> None:
        super().__init__()

        self.rcv_queue = rcv_queue
        self.result_queue = result_queue
        self.websocket = websocket
        self.service = service

    @abstractmethod
    async def listen_loop(self, ):
        pass

    @abstractmethod
    async def send_loop(self):
        pass

    @abstractmethod
    async def process_loop(self):
        pass

    @abstractmethod
    async def kill(self):
        pass





