from ..services.openai_service import OpenAIClient
from ..services.template_service import TemplateService
from ..services.conversation_service import ConversationService

from data.models.conversation.chat_message import ChatMessage

class ChatHandler:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.template_service = TemplateService()
        self.conversation_service = ConversationService()

    def get_chat_completion(self, template_name: str, template_version: int, chat_message: ChatMessage):
        return self.conversation_service.new_chat_message(chat_message.conversation_id, chat_message)





