from typing import List, Any, Dict
from pydantic import BaseModel, Field


class EmbeddedChunk(BaseModel):
    chunk_id: str
    content: str
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
