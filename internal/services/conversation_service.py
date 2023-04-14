from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key
from .pinecone_service import PineconeService, PineConeItem, PineConeChatItem, PineConeIndexes

from data.models.conversation.chat_message import ChatMessage, ChatRoles
from data.models.conversation.conversation import Conversation

from .agent_service import AgentService
from .template_service import TemplateService
from .openai_service import OpenAIClient

from pydantic import BaseModel

from typing import Any, List

class ConversationChatResult(BaseModel):
    model_response: Any
    knowledge_docs: Any
    chat_message_history: Any

class ConversationService:
    def __init__(self):
        self.dynamodb_service = DynamoDBService('Conversation')
        self.chat_dynamodb_service = DynamoDBService('ChatMessage')

        self.pinecone_service = PineconeService()
        self.agent_service = AgentService()
        self.template_service = TemplateService()
        self.openai_client = OpenAIClient()

        # TODO: Change after upgrading pinecone to support more indexes
        self.MEDICAL_INDEX = 'medical-documents'
        PineconeService.load_index(self.MEDICAL_INDEX)

        self.KNOWLEDGE_NAMESPACE = 'medical-docs'
        self.HISTORY_NAMESPACE = 'chat-message'

    def get_conversation(self, user_id: str, conversation_id: str) -> ItemCrudResponse:
        id_key = { 'user_id': user_id, 'id': conversation_id }

        return self.dynamodb_service.get_item(None, id_keys=id_key)
    
    def create_conversation(self, conversation: Conversation) -> ItemCrudResponse:
        # Set id and timestamps
        conversation = Conversation.set_id(conversation)
        conversation = Conversation.set_date_times(conversation)

        return self.dynamodb_service.update_item(conversation)

    def list_conversation(self, user_id: str) -> ItemCrudResponse:
        query = Key('user_id').eq(user_id)

        return self.dynamodb_service.scan_table(query)
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> ItemCrudResponse:
        # Check that conversation exists
        id_key = { 'user_id': user_id, 'id': conversation_id }

        existing_conversation = self.dynamodb_service.get_item(
            None,
            id_keys=id_key
        )

        if not existing_conversation.success or existing_conversation.Item == {}:
            return existing_conversation
        
        # Delete conversation if it exists
        return self.dynamodb_service.delete_item(None, item_key=id_key)
    
    def get_chat_message(self, conversation_id: str, id: str):
        id_keys = { 'conversation_id': conversation_id, 'id': id }

        return self.dynamodb_service.get_item(None, id_keys=id_keys)
    
    def list_chat_messages(self, conversation_id: str):
        query_filter = Key('conversation_id').eq(conversation_id) # & Key('field').eq(value)

        return self.chat_dynamodb_service.scan_table(query_filter)
    
    def calculate_split(self, length_messages: int, plain_text_messages, max_chars):
        # Can include full messages
        if length_messages < max_chars:
            return -1
        
        return int(length_messages / len(plain_text_messages))
    
    def chunk_message(self, max_split, messages):
        chunked_messages = []

        for message in messages:
            if len(message) <= max_split:
                chunked_messages.append(message)

            else:
                chunked_messages += message[: max_split]

        return '|END|'.join(chunked_messages)
    
    def mix_knowledge_and_history(self, knowledge_docs: PineConeItem, history_docs: PineConeChatItem, template, max_chars=4096):
        # Calculate portions of space that history and knowledge will have
        # First, let's try and give our model 1000 tokens to use
        model_max_tokens = 1000
        
        max_context_chars = max_chars - model_max_tokens - len(template)

        # Start experimentation with a 70/30 split of background knowledge to chat history
        knowledge_portion = 0.7
        history_portion = 0.3

        max_knowledge_tokens = int(max_context_chars * knowledge_portion)
        max_history_tokens = int(max_context_chars * history_portion)

        # Start with chat history first, to see if there will be extra space for the docs and completion
        length_history_messages = 0
        history_messages = []
        history_chat_messages = []

        # Docs are ranked by relevance in order, so the first few should get larger share
        history_doc_portions = [0.5, 0.3, 0.2]
        for index, history_doc in enumerate(history_docs):
            conversation_id = history_doc.metadata['conversation_id']
            _id = history_doc.metadata['id']

            chat_message_result = self.get_chat_message(conversation_id, _id)
            if not chat_message_result.success or chat_message_result.Item == {}:
                continue

            chat_message = chat_message_result.Item
            history_chat_messages.append(chat_message)

            message = chat_message['message']
            max_message_length = int(max_history_tokens * history_doc_portions[index])

            if len(message) <= max_message_length:
                length_history_messages += len(message)
                history_messages.append(message)

            else:
                message = message[:max_message_length]
                length_history_messages += len(message)
                history_messages.append(message)

        # Check if there are any extra tokens
        extra_tokens = max_history_tokens - length_history_messages

        # If there are, add half of them to model output, and half to knowledge context
        if extra_tokens > 0:
            max_knowledge_tokens += int(extra_tokens * 0.5)
            model_max_tokens += int(extra_tokens * 0.5)

        length_knowledge_messages = 0
        knowledge_messages = []

        # Let's give the knowledge docs a closer split, they tend to relate relatively equally
        knowledge_doc_portions = [0.45, 0.35, 0.2]
        for index, knowledge_doc in enumerate(knowledge_docs):
            message = knowledge_doc.metadata['PlainText']

            max_message_length = int(max_knowledge_tokens * knowledge_doc_portions[index])

            if len(message) <= max_message_length:
                length_knowledge_messages += len(message)
                knowledge_messages.append(message)

            else:
                message = message[:max_message_length]
                length_knowledge_messages += len(message)
                knowledge_messages.append(message)

        # Give model any extra space
        template = template.replace('{relevant_information}', '\nINFO:'.join(knowledge_messages))
        template = template.replace('{history}', '\nINFO:'.join(history_chat_messages))
        system_message = { 'role': ChatRoles.SYSTEM_ROLE.value, 'content': template }

        # Now, we have the background knowledge, and context of the message
        return system_message
    
    def new_chat_message(self, conversation_id: str, chat_message: ChatMessage):
        # First, grab top 3 documents that are most relevant to message
        knowledge_base_query = self.pinecone_service.plain_text_query(self.MEDICAL_INDEX, self.KNOWLEDGE_NAMESPACE, chat_message.message, top_k=3)
        knowledge_docs = knowledge_base_query.Item

        # Then, grab the top 3 message from history based on message relevance
        history_base_query = self.pinecone_service.plain_text_query(self.MEDICAL_INDEX, self.HISTORY_NAMESPACE, chat_message.message, top_k=3)
        history_docs = history_base_query.Item

        # Now, load the conversation and agent, so we can handle the chat request
        conversation = self.get_conversation(chat_message.user_id, conversation_id)

        if not conversation.success or conversation.Item == {}:
            return conversation
        
        # Load agent
        conversation = conversation.Item
        agent = self.agent_service.get_agent(chat_message.user, conversation['agent_name'])

        template_name = conversation['template_name']
        template_owner = conversation['template_owner']

        template = self.template_service.get_template(template_name, 2)

        system_message = self.mix_knowledge_and_history(knowledge_docs, history_docs, template.Item['template'])
        user_message = {'role': 'user', 'content': chat_message.message}

        completion = self.openai_client.get_chat_completion(messages=[
            system_message,
            user_message
        ])

        ai_message = OpenAIClient.decode_completion_to_chat_message(completion, chat_message)

        # After obtaining completion, store the chat data
        self.store_chat_message(chat_message)
        self.store_chat_message(ai_message)

        return ConversationChatResult(
            model_response=ai_message,
            knowledge_docs=knowledge_docs,
            chat_message_history=history_docs
        )
    
    def store_chat_message(self, chat_message):
        # Storing chat messages efficiently is really important
        # We need to leverage embeddings for this, however
        # we don't want to bog down our pinecone db with unnecessary data and make it slow

        # We also, don't want to "double dip" on what will be the hardest data model to scale
        # For Now, let's store the embedding of the chat message in pinecone database,
        # and an index to that message, with text in dynamodb

        # Obtain embedding from chat_message
        message = chat_message.message
        message_embedding = self.openai_client.get_embeddings(message)

        chat_message = ChatMessage.set_id(chat_message)
        chat_message = ChatMessage.set_datetimes(chat_message)

        # Store embedding in pinecone
        if chat_message.agent_name is None:
            chat_message.agent_name = 'None'

        pinecone_chat_item = PineConeChatItem.from_chat_message(chat_message, message_embedding)
        upsert_result = self.pinecone_service.upsert_data(PineConeIndexes.CHAT_INDEX.value, pinecone_chat_item)
        
        # After storing the pinecone embedding, store the message in dynamodb, so we can keep text and vectors separate
        chat_message_crud_result = self.chat_dynamodb_service.update_item(chat_message)

        return ItemCrudResponse(
            Item= {
                'PineconeItem': upsert_result,
                'ChatMessage': chat_message_crud_result
            },
            success=True,
            exception=None
        )

        
