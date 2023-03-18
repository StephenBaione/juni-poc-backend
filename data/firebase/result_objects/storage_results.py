import pydantic

from typing import Optional, Any

class FileOperationResult(pydantic.BaseModel):
    success: bool
    message: str
    file_name: str
    data: Optional[Any]