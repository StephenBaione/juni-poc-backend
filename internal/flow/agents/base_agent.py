import abc

from typing import Any, List

from data.models.agents.agent import Agent, AgentInputTypes

from pydantic import BaseModel

class BaseAgent(abc.ABC):
    def __init__(self, agent: Agent, consumer: "BaseAgent") -> None:
        self.agent = agent
        self.consumer = consumer


    @abc.abstractmethod
    def consume(self, data, response_dict): # items are an array containing the collected data from each agent to show to user
        pass

    def broadcast(self, data: Any, reponse_dict):
        return self.consumer.consume(data, response_dict=reponse_dict)
        # for consumer in self.consumers:
        #     consumer.consume(data)
        



