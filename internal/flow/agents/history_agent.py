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

    async def consume(self, chat_message: ChatMessage, response_dict):
        # Check to see if the start event has been set for connection
        await self.check_and_set_on_start()

        # TODO: Make sure that the chat message are sorted by most recent first

        # Get list of messages from dynamodb
        result = self.conversation_service.list_chat_messages(chat_message.conversation_id, chat_message.user_id)
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
                id = message.get('id'),
                role = message.get('role'),
                sender = message.get('sender'),
                conversation_id = message.get('conversation_id'),
                user = message.get('user'),
                user_id = message.get('user_id'),
                agent_name = message.get('agent_name'),
                message = message
            )

            # Add message and update total length
            messages.append(new_chat_message)
            total_length += message_length

        self.connection.input_queue.put(messages)
        self.connection.on_output.set()
