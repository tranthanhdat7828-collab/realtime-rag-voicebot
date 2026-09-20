from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default_session"


class QueryReponse(BaseModel):
    question: str
    answer: str
    has_context: bool = False
