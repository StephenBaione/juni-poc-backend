from pydantic import BaseModel

from typing import Optional

import urllib.parse

class CallRequest:
    history: str = ''
    text: str = ''
    voice: str = ''
    model: str = ''
    
    initiated_conversation: bool = False

    def to_param_string(self):
        params = {
            'history': self.history,
            'text': self.text,
            'voice': self.voice,
            'model': self.model,
            'initiated_conversation': self.initiated_conversation
        }

        param_string = f"{'&'.join([f'{key}={value}' for key, value in params.items() if value is not None and value != ''])}"
        return urllib.parse.quote(param_string)

