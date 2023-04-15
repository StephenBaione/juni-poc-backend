from queue import Queue

from data.models.conversation.chat_message import ChatMessage

from typing import List

class ChatOutput:
    def __init__(self, connection = None) -> None:
        self.connection = connection

    def set_connection(self, connection):
        self.connection = connection

    def consume(self, items: List, response_dict):
        return items, response_dict