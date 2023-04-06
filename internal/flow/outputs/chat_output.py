from queue import Queue

from data.models.conversation.chat_message import ChatMessage

from typing import List

class ChatOutput:
    def __init__(self) -> None:
        pass

    def consume(self, items: List, response_dict):
        return items, response_dict