import abc

from typing import Any, List

from data.models.agents.agent import Agent

class BaseAgent(abc.ABC):
    def __init__(self, agent: Agent, consumer) -> None:
        self.agent = agent
        self.consumer = consumer

    @abc.abstractmethod
    def consume(self, data):
        pass



