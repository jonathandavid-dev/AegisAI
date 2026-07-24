from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    """Schema representing semantic search requests."""
    query: str = Field(..., min_length=1, description="The text query to retrieve matches for.")
    top_k: int = Field(10, ge=1, le=100, description="Number of top chunks to return.")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filtering key-value constraints.")

class SearchResultItem(BaseModel):
    """Schema representing an individual retrieved segment match with relevance score."""
    document_id: int
    chunk_id: str
    filename: str
    page_number: int
    chunk_index: int
    score: float
    content: str

class SearchResponse(BaseModel):
    """Schema representing the collection of matching chunks and processing statistics."""
    query: str
    results: List[SearchResultItem]
    processing_time_ms: float
