from typing import Any, List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., description="Pertanyaan dalam bahasa alami (Natural Language)")

class QueryResponse(BaseModel):
    question: str
    sql: str
    result: List[Any]
    answer: str
    error: Optional[str] = None
