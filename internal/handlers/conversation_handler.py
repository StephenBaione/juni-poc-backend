

from data.models.conversation.conversation import Conversation
from data.models.conversation.chat_message import ChatMessage

from ..services.conversation_service import ConversationService, ItemCrudResponse

class ConversationHandler:
    def __init__(self) -> None:
        self.conversation_service = ConversationService()

    def handle_create_conversation(self, converstaion: Conversation) -> ItemCrudResponse:
        return self.conversation_service.create_conversation(converstaion)

    def handle_get_conversation(self, user_id: str, conversation_id: str) -> ItemCrudResponse:
        return self.conversation_service.get_conversation(user_id, conversation_id)
    
    def handle_list_conversation(self, user_id: str) -> ItemCrudResponse:
        return self.conversation_service.list_conversation(user_id)
    
    def handle_delete_conversation(self, user_id, conversation_id) -> ItemCrudResponse:
        return self.conversation_service.delete_conversation(user_id, conversation_id)
    
    def handle_new_chat_message(self, conversation_id: str, chat_message: ChatMessage) -> ItemCrudResponse:
        return self.conversation_service.new_chat_message(conversation_id, chat_message)

    def handle_store_chat_message(self, chat_message: ChatMessage) -> ItemCrudResponse:
        return self.conversation_service.store_chat_message(chat_message)
    
    def handle_list_chat_messages(self, conversation_id: str) -> ItemCrudResponse:
        return self.conversation_service.list_chat_messages(conversation_id)
