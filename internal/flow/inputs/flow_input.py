from typing import Any

import abc

from queue import Queue

from .input_events import InputExecutionEvents, InputEvent, EventSenders

class FlowInput(abc.ABC):
    def __init__(self, _id, data: Any, producers: list, consumers: list, events: InputExecutionEvents) -> None:
        self._id = _id
        self.producers = producers
        self.consumers = consumers

        self.data_buffer = Queue()
        self.events = InputExecutionEvents()

        