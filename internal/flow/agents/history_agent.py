from .base_agent import BaseAgent

# from internal.services.chat_service import ChatService
from internal.services.conversation_service import ConversationService
from data.models.conversation.chat_message import ChatMessage

from internal.services.dynamodb_service import DynamoDBService

from typing import List

from ..connections.sequential_connection import SequentialConnection

class HistoryAgent(BaseAgent):
    def __init__(self, agent, connection: SequentialConnection = None, max_size=1000) -> None:
        """A HistoryAgent has the ability to reference the history of a session.
        For now, this means that a history agent is able to reference the chat history between a user and an agent,
        With the intent of supplying that history to provide model with conversational context

        Args:
            agent (Agent): The Agent model that is associated with current history agent
            connection (SequentialConnection): A connection object responsible for handling data transfer between agents
            max_size (int, optional): Maximum token size for history agent output. Defaults to 1000.
        """
        super().__init__(agent, connection)

        # self.chat_service = ChatService()
        self.conversation_service = ConversationService()
        self.chat_dynamodb_service = DynamoDBService('ChatMessage')

        self.max_size = max_size

    async def consume(self, chat_messages: List[ChatMessage]):
        # Check to see if the start event has been set for connection
        # TODO: Make sure that the chat message are sorted by most recent first

        # Get list of messages from dynamodb
        chat_message = chat_messages[0]
        result = self.conversation_service.list_chat_messages(chat_message.conversation_id)
        chat_message_list = result.Item

        # Create a list of chat messages
        messages = []
        total_length = 0
        for chat_message_item in chat_message_list:
            message = chat_message_item['message']
            message_length = len(message)

            # Only include chunk of message if greater than max length
            if total_length + message_length > self.max_size:
                message = message[:total_length - message_length]
                message_length = len(message)

            # For each dict message, create a ChatMessage object
            new_chat_message = ChatMessage(
                id = chat_message_item.get('id'),
                role = chat_message_item.get('role'),
                sender = chat_message_item.get('sender'),
                conversation_id = chat_message_item.get('conversation_id'),
                user = chat_message_item.get('user'),
                user_id = chat_message_item.get('user_id'),
                agent_name = self.agent.name,
                message = message,
                flow_id=chat_message.flow_id
            )

            # Add message and update total length
            messages.append(new_chat_message)
            total_length += message_length

        self.conversation_service.store_chat_message(chat_message)
        return messages
