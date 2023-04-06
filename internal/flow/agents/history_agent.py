from .base_agent import BaseAgent

# from internal.services.chat_service import ChatService
from internal.services.conversation_service import ConversationService
from data.models.conversation.chat_message import ChatMessage

from internal.services.dynamodb_service import DynamoDBService

from typing import List

class HistoryAgent(BaseAgent):
    def __init__(self, agent, consumer) -> None:
        super().__init__(agent, consumer)

        # self.chat_service = ChatService()
        self.conversation_service = ConversationService()
        self.chat_dynamodb_service = DynamoDBService('ChatMessage')

    def consume(self, chat_message: ChatMessage, response_dict):
        # get list of messages from dynamodb
        # TODO: handle pagination for large conversations
        result = ConversationService.list_user_chat_messages(self, chat_message.conversation_id, chat_message.user_id)
        data = result.Item

        # create a list of chat messages
        messages = []
        for message in data:
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

        # append the latest chat message
        messages.append(chat_message)

        # TODO: messages should not exceed a certain max token size, so cut off the oldest messages. oldest message is the first message in the list

        return self.broadcast(messages, response_dict)
