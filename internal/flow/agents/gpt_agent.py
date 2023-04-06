from .base_agent import BaseAgent

from internal.services.openai_service import OpenAIClient
from internal.services.chat_service import ChatService

from data.models.conversation.chat_message import ChatMessage

from typing import List

class GPTAgent(BaseAgent):
    def __init__(self, agent, consumer) -> None:
        super().__init__(agent, consumer)

        self.openai_service = OpenAIClient()
        self.chat_service = ChatService()

    def consume(self, chat_messages: List[ChatMessage], response_dict):
        completion = self.openai_service.get_chat_completion(messages=ChatMessage.as_openai_input(chat_messages))

        agent_chat_message = OpenAIClient.decode_completion_to_chat_message(completion, chat_messages[0])

        self.chat_service.store_chat_message(agent_chat_message)

        response_dict['GPT'] = agent_chat_message
        return self.broadcast(agent_chat_message, response_dict)
