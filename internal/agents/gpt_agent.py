from .base_agent import BaseAgent

from ..services.openai_service import OpenAIClient

from data.models.conversation.chat_message import ChatMessage

from typing import Callable

class GPTAgent(BaseAgent):
    def __init__(self, agent, consumer: BaseAgent, producer: BaseAgent) -> None:
        super().__init__(agent, consumer, producer)

        self.messages = []
        self.openai_service = OpenAIClient()

    def consume_input(self, messages: list):
        return super().consume_input(input)
    
    def execute(self) -> ChatMessage:
        messages = self.messages

        completion = self.openai_service.get_chat_completion(messages=messages)

        if len(self.consumers) > 0:
            return self.chain_consumers(completion)

    def chain_consumers(self, completion):
        return self.consumer.execute(completion)

