from .base_agent import BaseAgent

from internal.services.openai_service import OpenAIClient
from internal.services.chat_service import ChatService

from data.models.conversation.chat_message import ChatMessage

from ..connections.sequential_connection import SequentialConnection

from typing import List

class GPT4Agent(BaseAgent):
    def __init__(self, agent, node_cfg, connection: SequentialConnection = None) -> None:
        super().__init__(agent, node_cfg, connection)

        self.openai_service = OpenAIClient()
        self.chat_service = ChatService()

    async def consume(self, chat_messages: List[ChatMessage]):
        if not isinstance(chat_messages, list):
            chat_messages = [chat_messages]

        completion = self.openai_service.get_chat_completion(messages=ChatMessage.as_openai_input(chat_messages), model='gpt-4')
        agent_chat_message = OpenAIClient.decode_completion_to_chat_message(completion, chat_messages[0], self.agent.name)

        self.chat_service.store_chat_message(agent_chat_message)

        return agent_chat_message
