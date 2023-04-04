from asyncio import Event

from typing import Any

from enum import Enum

class InputExecutionEvents:
    def __init__(self) -> None:
        self.pause_event = Event()
        self.start_event = Event()
        self.stop_event = Event()

class EventSenders(Enum):
    TEXT_INPUT = 'text_input'

class EventTypes(Enum):
    SEND_EVENT = 'send_event'
    STOP_EVENT = 'stop_event'
    PAUSE_EVENT = 'pause_event'
    START_EVENT = 'start_event'

class InputEvent:
    def __init__(self, data: Any, sender: str, event_type: str) -> None:
        self.data = data
        self.sender = sender
        self.event_type = event_type

class SendEvent(InputEvent):
    def __init__(self, data: Any, sender: str) -> None:
        event_type = EventTypes.SEND_EVENT

        super().__init__(data, sender, event_type)

        


