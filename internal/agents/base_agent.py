import abc

from typing import Any, List

from data.models.agents.agent import Agent

class BaseAgent(abc.ABC):
    def __init__(self, agent: Agent, consumer: "BaseAgent", producer: "BaseAgent") -> None:
        self.agent = agent
        self.consumer = consumer
        self.producer = producer

    @abc.abstractmethod
    def consume_input(self, input: Any):
        pass

    @abc.abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass

    def chain_consumers(self, data: Any):
        self.consumer.consume_input(data)

        return self.consumer.execute(data)


