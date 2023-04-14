from pydantic import BaseModel

from typing import Optional

from datetime import datetime

from uuid import uuid4

class Conversation(BaseModel):
    id: Optional[str]
    nickname: str
    user_id: str
    flow_id: str

    created_at: Optional[str]
    updated_at: Optional[str]

    @staticmethod
    def set_id(conversation: "Conversation") -> "Conversation":
        conversation.id = str(uuid4())

        return conversation

    @staticmethod
    def set_date_times(conversation: "Conversation") -> "Conversation":
        conversation.created_at = str(datetime.now())
        conversation.updated_at = str(datetime.now())

        return conversation
    
    @staticmethod
    def set_updated_at(conversation: "Conversation") -> "Conversation":
        conversation.updated_at = str(datetime.now())

        return conversation

