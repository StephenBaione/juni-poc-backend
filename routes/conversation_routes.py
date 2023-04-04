from fastapi import APIRouter, Body

from data.models.conversation.conversation import Conversation
from data.models.conversation.chat_message import ChatMessage

from internal.handlers.conversation_handler import ConversationHandler

conversation_router = APIRouter(prefix='/conversation', tags=['Conversation'])
conversation_handler = ConversationHandler()

@conversation_router.post('/create')
async def create_conversation(conversation: Conversation = Body(...)):
    return conversation_handler.handle_create_conversation(conversation)

@conversation_router.get('/get/{user_id}/{conversation_id}')
async def get_conversation(user_id: str, conversation_id: str):
    return conversation_handler.handle_get_conversation(user_id, conversation_id)

@conversation_router.delete('/delete/{user_id}/{conversation_id}')
async def delete_conversation(user_id: str, conversation_id: str):
    return conversation_handler.handle_delete_conversation(user_id, conversation_id)

@conversation_router.get('/list/{user_id}')
async def list_conversations(user_id: str):
    return conversation_handler.handle_list_conversation(user_id)

@conversation_router.post('/chat/store', tags=['Chat'])
async def store_chat_message(chat_message: ChatMessage):
    return conversation_handler.handle_store_chat_message(chat_message)

@conversation_router.post('/chat/{conversation_id}', tags=['Chat'])
async def new_chat_message(conversation_id: str, chat_message: ChatMessage = Body(...)):
    return conversation_handler.handle_new_chat_message(conversation_id, chat_message)

@conversation_router.get('/chat/{conversation_id}/list', tags=['Chat'])
async def list_chat_messages(conversation_id: str):
    return conversation_handler.handle_list_chat_messages(conversation_id)

