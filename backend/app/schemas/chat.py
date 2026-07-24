from typing import List, Dict, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Schema representing user RAG chat queries."""
    question: str = Field(..., min_length=1, description="The grounding question to answer using context.")
    top_k: int = Field(5, ge=1, le=20, description="Max context chunks to retrieve.")
    conversation_id: int | None = Field(None, description="Optional conversation session ID to append this turn to.")
    stream: bool = Field(False, description="Flag indicating if response should be streamed via Server-Sent Events (SSE).")


class ChatCitationItem(BaseModel):
    """Schema representing an individual document chunk source citation."""
    document_id: int
    filename: str = Field(..., alias="filename")
    page_number: int
    chunk_index: int

    model_config = {
        "populate_by_name": True
    }

class ChatResponse(BaseModel):
    """Schema representing the generated answer, citations, memory, and tool execution logs."""
    conversation_id: int
    question: str
    rewritten_query: str
    answer: str
    citations: List[ChatCitationItem]
    retrieval: Dict[str, Any]
    memory: Dict[str, Any]
    tool_execution: Dict[str, Any] | None = None
    processing_time_ms: float
