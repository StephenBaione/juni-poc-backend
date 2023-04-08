from internal.services.pinecone_service import PineconeService, ItemCrudResponse
from internal.services.chat_service import ChatService

from .base_agent import BaseAgent

from ..connections.sequential_connection import SequentialConnection

from data.models.agents.agent import Agent
from data.models.conversation.chat_message import ChatMessage, ChatRoles

class KnowledgeAgent(BaseAgent):
    def __init__(self, agent, connection: SequentialConnection = None, index: str = 'medical-documents', namespace: str = 'medical-docs') -> None:
        super().__init__(agent, connection)

        self.index = index
        self.namespace = namespace

        self.pinecone_service = PineconeService()
        self.pinecone_service.load_index(index)

    def set_options(self, index: str):
        self.pinecone_service.load_index(index)
        self.index = index

    def set_namespace(self, namespace: str):
        self.namespace = namespace

    # TODO: For now assume chat message, implement other types later
    async def consume(self, chat_message: ChatMessage, max_tokens=1000):
        await self.check_and_set_on_start()

        # Extract text from chat message
        text = chat_message.message

        # Query the pinecone index for best matching results
        query_results: ItemCrudResponse = self.pinecone_service.plain_text_query(self.index, self.namespace, text)
        
        # Grab the items and create the knowledge template
        knowledge_items = query_results.Item
        
        # Parse through the returned knowledge items and grab the plain text
        knowledge_messages = []
        total_length = 0
        for knowledge_item in knowledge_items:
            message = knowledge_item.metadata['PlainText']

            # Make sure that token length stays below max length
            tokens_left = max_tokens - total_length
            if len(message) > tokens_left:
                message = message[:max_tokens - total_length]

            # Append message
            knowledge_message = ChatMessage(
                role=ChatRoles.AI_ROLE.value,
                sender=self.agent.name,
                conversation_id=chat_message.conversation_id,
                user=chat_message.user,
                user_id=chat_message.user_id,
                agent_name=self.agent.name,
                message=message
            )

            message_length = len(message)
            total_length += message_length
            knowledge_messages.append(knowledge_message)

        self.connection.input_queue.put(knowledge_messages)
        self.connection.on_output.set()
