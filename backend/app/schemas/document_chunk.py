from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document_chunk import ChunkEmbeddingStatus

class DocumentChunkResponse(BaseModel):
    """Schema representing structured parsed segments of a document."""
    id: int
    document_id: int
    chunk_index: int
    page_number: int | None
    content: str
    character_count: int
    embedding_status: ChunkEmbeddingStatus
    embedded_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
