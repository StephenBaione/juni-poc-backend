from fastapi import APIRouter, Body
from internal.handlers.chat_handler import ChatHandler

from data.models.conversation.chat_message import ChatMessage

chat_router = APIRouter(prefix='/chat', tags=['Conversation', 'Chat'])

chat_handler = ChatHandler()

# @chat_router.post('/chat_completion')
# def get_chat_completion(template_name: str, template_version: int, chat_message: ChatMessage = Body(...)):
#     return chat_handler.get_chat_completion(template_name, template_version, chat_message)

@chat_router.post('/new_chat_message')
async def new_chat_message(chat_message: ChatMessage = Body(...)):
    return chat_handler.handle_new_chat_message(chat_message)