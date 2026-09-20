from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class Chunk(BaseModel):
    chunk_id: Optional[str] = None
    content: str
    enriched_content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
