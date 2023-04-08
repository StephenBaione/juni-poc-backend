from .base_agent import BaseAgent

# from internal.services.chat_service import ChatService
from internal.services.conversation_service import ConversationService
from data.models.conversation.chat_message import ChatMessage

from internal.services.dynamodb_service import DynamoDBService

from typing import List

class HistoryAgent(BaseAgent):
    def __init__(self, agent, consumer, max_size=1000) -> None:
        super().__init__(agent, consumer)

        # self.chat_service = ChatService()
        self.conversation_service = ConversationService()
        self.chat_dynamodb_service = DynamoDBService('ChatMessage')

        self.max_size = max_size

    def consume(self, chat_message: ChatMessage, response_dict):
        # TODO: Make sure that the chat message are sorted by most recent first

        # get list of messages from dynamodb
        result = self.conversation_service.list_chat_messages(chat_message.conversation_id, chat_message.user_id)
        data = result.Item

        # create a list of chat messages
        messages = []
        total_length = 0
        for message in data:
            message_length = len(message)

            # Only include portion of message if greater than max length
            if total_length + message_length > self.max_size:
                message = message[:total_length - message_length]
                message_length = len(message)

            # for each dict message, create a ChatMessage object
            new_chat_message = ChatMessage(
                id = message.get('id'),
                role = message.get('role'),
                sender = message.get('sender'),
                conversation_id = message.get('conversation_id'),
                user = message.get('user'),
                user_id = message.get('user_id'),
                agent_name = message.get('agent_name'),
                message = message.get('message'),
            )

            messages.append(new_chat_message)
            total_length += message_length

        # append the latest chat message
        messages.append(chat_message)
        return self.broadcast(messages, response_dict)
