from typing import Optional

from pydantic import BaseModel

import json

from uuid import uuid4, uuid1

from datetime import datetime

from enum import Enum

from ..item_id import ItemId

class ChatRoles(Enum):
    SYSTEM_ROLE = 'system'
    AI_ROLE = 'assistant'
    USER_ROLE = 'user'

class ChatSenders(Enum):
    SYSTEM_SENDER = 'system'
    AI_SENDER = 'ai'
    USER_SENDER = 'user'

class ChatMessage(BaseModel):
    id: Optional[str] = None
    
    # Role should be a chosen from above roles object
    role: str
    sender: str

    conversation_id: str

    user: str
    user_id: str

    agent_name: str

    message: str

    created_at: Optional[str]
    updated_at: Optional[str]

    def __str__(self):
        return json.dumps(dict(self))
    
    @staticmethod
    def set_id(chat_message: "ChatMessage") -> "ChatMessage":
        # Use uuid1, so that id is always increasing, which will yield in order queries
        chat_message.id = ItemId.generate_item_id(sequential=True)

        return chat_message

    @staticmethod
    def set_datetimes(chat_message: "ChatMessage") -> "ChatMessage":
        created_at = updated_at = str(datetime.now())

        chat_message.created_at = created_at
        chat_message.updated_at = updated_at

        return chat_message
    
    def as_template_message(self, chat_message) -> str:
        pass

class TemplateMessage:
    def __init__(self, chat_message: ChatMessage) -> None:
        if chat_message.sender == ChatSenders.SYSTEM_SENDER.value:
            self.template_text = f""

    def format_template_text(sender: ChatSenders, chat_message: ChatMessage):
        message = chat_message.message

        sender = chat_message.sender

        if sender == ChatSenders.SYSTEM_SENDER.value:
            return f"Personamatic: {message}"
        
        elif sender == ChatSenders.AI_SENDER.value:
            return f"{chat_message.model}: {message}"
        
        elif sender == ChatSenders.USER_SENDER.value:
            return f"{chat_message.user}: {message}"

