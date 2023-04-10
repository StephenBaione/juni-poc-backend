import abc

from typing import Any, List

from data.models.agents.agent import Agent

from ..connections.sequential_connection import SequentialConnection

class BaseAgent(abc.ABC):
    def __init__(self, agent: Agent, connection: SequentialConnection = None) -> None:
        self.agent = agent
        self.connection = connection


    @abc.abstractmethod
    async def consume(self, data, response_dict):
        """The Consume function receives the data from a connection and starts agent execution.
        It should only receive and return the data that the specific model is responsible for.

        Args:
            data (Any): The data that is sent to the agent to process
            response_dict (dict): A running dictionary that tracks all agent outputs.
        """
        pass

    def broadcast(self, data: Any, reponse_dict):
        return self.consumer.consume(data, response_dict=reponse_dict)
        # for consumer in self.consumers:
        #     consumer.consume(data)

    # Make this function asynchronous
    async def start_connection_receive(self):
        await self.connection.receive()

    async def check_and_set_on_start(self):
        if not self.connection.on_start.is_set():
            await self.connection.receive()
            self.connection.on_start.set()
