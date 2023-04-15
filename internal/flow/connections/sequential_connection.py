
import asyncio
from asyncio import Event

from queue import Queue

class ConnectionInput:
    def __init__(self, on_start: Event, on_output: Event, input_queue: Queue, response_dict: dict) -> None:
        self.on_start = on_start
        self.on_output = on_output
        self.input_queue = input_queue
        self.response_dict = response_dict

    @staticmethod
    def get_instance() -> "ConnectionInput":
        return ConnectionInput(
            on_start=Event(),
            on_output=Event(),
            input_queue=Queue(),
            response_dict={}
        )

class SequentialConnection:
    def __init__(self, connection_input: ConnectionInput) -> None:
        """The SequentialConnection object is responsible for handling a connection from one producer.
        The connection receives the data from the producer and sends it to the consumer.

        Args:
            producer_agent (BaseAgent): _description_
            consumer_agent (BaseAgent): _description_
            connection_input (ConnectionInput): _description_
        """
        self.producer_agent = None
        self.consumer_agents = []

        self.on_start = connection_input.on_start
        self.on_output = connection_input.on_output
        self.input_queue = connection_input.input_queue
        self.response_dict = connection_input.response_dict

    def set_producer_agent(self, agent):
        self.producer_agent = agent

    def add_consumer_agent(self, agent):
        self.consumer_agents.append(agent)

    async def receive(self):
        # After the receive loop has been started, we have to free up execution and wait until the on_output event is set
        # When the on_output event is set (i.e. the producer agent sends its data, the data is passed along to the consumer)
        await self.on_output.wait()
        
        try:
            response_dict = self.response_dict
            producer_data = self.input_queue.get(block=False)

            for consumer_agent in self.consumer_agents:
                return await consumer_agent.consume([producer_data], response_dict)

        except Exception as e:
            print(e)
        
