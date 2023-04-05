from pydantic import BaseModel

from typing import Optional

from uuid import uuid4

from datetime import datetime

from enum import Enum

class OutputtNodeIOTypes(Enum):
    CHAT = 'ChatOutput'

class OutputNode(BaseModel):
    id: Optional[str]

    _type: str

    @staticmethod
    def set_id(input_node: "OutputNode") -> "OutputNode":
        input_node.id = str(uuid4())

        return input_node

    @staticmethod
    def set_date_times(input_node: "OutputNode") -> "OutputNode":
        input_node.created_at = str(datetime.now())
        input_node.updated_at = str(datetime.now())

        return input_node

