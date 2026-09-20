from pydantic import BaseModel
from typing import Dict, Any


class Document(BaseModel):
    content: str
    metadata: Dict[str, Any]
