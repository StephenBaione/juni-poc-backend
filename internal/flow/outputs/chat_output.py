from queue import Queue

from data.models.conversation.chat_message import ChatMessage

class ChatOutput:
    def __init__(self, output_queue: Queue) -> None:
        self.output_queue = output_queue

    def consume(self, chat_message: ChatMessage):
        self.output_queue.put(chat_message)