from .dynamodb_service import DynamoDBService, ItemCrudResponse, Key
from .openai_service import OpenAIClient
from .pinecone_service import PineconeService, PineConeItem, PineConeChatItem, PineConeIndexes

from data.models.conversation.chat_message import ChatMessage, ChatRoles

class ChatService:
    def __init__(self) -> None:
        self.chat_dynamodb_service = DynamoDBService('ChatMessage')

        self.pinecone_service = PineconeService()
        self.openai_client = OpenAIClient()

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
    
    def get_chat_completion(self, chat_message: ChatMessage) -> ChatMessage:
        result = self.store_chat_message(chat_message)

        if not result.success:
            return result

        openai_input = ChatMessage.as_openai_input(chat_message)
        completion = self.openai_client.get_chat_completion(openai_input)
        ai_message = OpenAIClient.decode_completion_to_chat_message(completion, chat_message)

        self.store_chat_message(ai_message)

        return ai_message