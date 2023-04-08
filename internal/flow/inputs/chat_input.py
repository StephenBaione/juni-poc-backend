from .flow_input import FlowInput
from .input_events import SendEvent, EventTypes, InputExecutionEvents

from data.models.conversation.chat_message import ChatMessage

from queue import Empty

from ..agents.base_agent import BaseAgent

from ..connections.sequential_connection import SequentialConnection

class ChatInput:
    def __init__(self) -> None:
        self.connection: SequentialConnection = None

    def set_connection(self, connection):
        self.connection = connection

    def consume_input(self, chat_message: ChatMessage):
        response_dict = {}
        return self.consumer.consume(chat_message, response_dict)


