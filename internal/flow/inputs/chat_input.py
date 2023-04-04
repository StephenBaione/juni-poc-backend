from .flow_input import FlowInput
from .input_events import SendEvent, EventTypes, InputExecutionEvents

from data.models.conversation.chat_message import ChatMessage

from queue import Empty

from ..agents.base_agent import BaseAgent


class ChatInput:
    def __init__(self, consumer: BaseAgent) -> None:
        self.consumer = consumer

    def consume_input(self, chat_message: ChatMessage):
        self.consumer.consume([chat_message])


