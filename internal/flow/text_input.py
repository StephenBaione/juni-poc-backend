from .flow_input import FlowInput
from .input_events import SendEvent, EventTypes, InputExecutionEvents

from data.models.conversation.chat_message import ChatMessage

from queue import Empty

class TextInput(FlowInput):
    def __init__(self, _id, chat_message: ChatMessage, producers: list, consumers: list, events: InputExecutionEvents) -> None:
        super().__init__(_id, chat_message, producers, consumers, events)

    def start(self):
        chat_message = self.data

        for consumer in self.consumers:
            consumer.start(chat_message)


