from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union

from uuid import uuid4

import json

class ChatMessage(BaseModel):
    id: str
    user: str
    sender: str
    model: str
    message: str
    created: Optional[str or None]
    updated: Optional[str or None]

    def __init__(__pydantic_self__, **data: Any) -> None:
        if data.get('id', None) is None:
            data['id'] = str(uuid4())

        super().__init__(**data)

    def __str__(self):
        return json.dumps(dict(self))



