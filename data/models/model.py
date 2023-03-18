import pydantic

from typing import Any

class Model(pydantic.BaseModel):
    name: str
    id: str
    external: bool
    owner: str
    created_at: str
    updated_at: str

    def __init__(__pydantic_self__, **data: Any) -> None:
        super().__init__(**data)
