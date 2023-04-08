from .base_agent import BaseAgent

from internal.services.openai_service import OpenAIClient
from internal.services.chat_service import ChatService

from data.models.conversation.chat_message import ChatMessage

from ..connections.sequential_connection import SequentialConnection

from typing import List

class GPTAgent(BaseAgent):
    def __init__(self, agent, connection: SequentialConnection = None) -> None:
        super().__init__(agent, connection)

        self.openai_service = OpenAIClient()
        self.chat_service = ChatService()

    async def consume(self, chat_messages: List[ChatMessage], response_dict):
        if not isinstance(chat_messages, list):
            chat_messages = [chat_messages]

        await self.check_and_set_on_start()

        completion = self.openai_service.get_chat_completion(messages=ChatMessage.as_openai_input(chat_messages))
        agent_chat_message = OpenAIClient.decode_completion_to_chat_message(completion, chat_messages[0])

        self.chat_service.store_chat_message(agent_chat_message)

        self.connection.input_queue.put(agent_chat_message)
        self.connection.on_output.set()
