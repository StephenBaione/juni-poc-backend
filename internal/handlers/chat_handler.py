from ..services.openai_service import OpenAIClient
from ..services.template_service import TemplateService
efrom ..services.chat_service import ChatService

from data.models.conversation.chat_message import ChatMessage

class ChatHandler:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.template_service = TemplateService()
        self.chat_service = ChatService()

    def handle_new_chat_message(self, chat_message: ChatMessage):
        return self.chat_service.get_chat_completion(chat_message)



