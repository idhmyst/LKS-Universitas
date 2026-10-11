from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(..., description="Pertanyaan dalam bahasa alami (Natural Language)")

class ChatResponse(BaseModel):
    sql: str
    chart: bool = False
    chartType: Optional[str] = None
    chartTitle: Optional[str] = None
    columns: List[str] = []
    data: List[Dict[str, Any]] = []

# Alias untuk backwards compatibility
QueryRequest = ChatRequest
