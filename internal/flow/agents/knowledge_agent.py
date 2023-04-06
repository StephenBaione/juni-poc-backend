from internal.services.pinecone_service import PineconeService, ItemCrudResponse
from internal.services.chat_service import ChatService

from .base_agent import BaseAgent


from data.models.agents.agent import Agent
from data.models.conversation.chat_message import ChatMessage, ChatRoles

class KnowledgeAgent(BaseAgent):
    def __init__(self, agent, consumers, index: str, namespace: str) -> None:
        super().__init__(agent, consumers)

        self.index = index
        self.namespace = namespace

        self.pinecone_service = PineconeService()
        self.pinecone_service.load_index(index)

        self.chat_service = ChatService()

    def set_options(self, index: str):
        self.pinecone_service.load_index(index)
        self.index = index

    def set_namespace(self, namespace: str):
        self.namespace = namespace

    # TODO: For now assume chat message, implement other types later
    def consume(self, chat_message: ChatMessage, response_dict, max_tokens=1000):
        # Get the message send with the chat message
        text = chat_message.message

        # Query the pinecone index for best matching results
        query_results: ItemCrudResponse = self.pinecone_service.plain_text_query(self.index, self.namespace, text)
        
        # If the pinecone search fails, return crud response
        if not query_results.success:
            return query_results
        
        # Grab the items and create the knowledge template
        knowledge_items = query_results.Item

        # TODO: Allow user to use their own template, restrict to one input variable names {knowledge}
        knowledge_template = \
            f"The following documents are the most relevant pieces of information. Reference them in your answer.\n" \
            "Background Knowledge:\n" \
            "{knowledge}"
        
        # Parse through the returned knowledge items and grab the plain text
        knowledge = ''
        for knowledge_item in knowledge_items:
            message = knowledge_item.metadata['PlainText']

            # Make sure that token length stays below max length
            tokens_left = max_tokens - len(knowledge_template) - len(knowledge)
            if len(message) > tokens_left:
                message = message[:tokens_left]
                knowledge += message
                break

            # Append message
            knowledge += message
            
        # Replace the varilable in template
        template = knowledge_template.replace('{knowledge}', message)

        # This is considered a system message
        role = ChatRoles.SYSTEM_ROLE.value
        response_message = ChatMessage(
            role=role,
            sender=chat_message.sender,
            conversation_id=chat_message.conversation_id,
            user=chat_message.user,
            user_id=chat_message.user_id,
            agent_name='knowledge',
            message=template
        )

        self.chat_service.store_chat_message(response_message)
        response_dict['knowledge'] = response_message
        return self.broadcast([response_message, chat_message], response_dict)

