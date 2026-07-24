from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus

class DocumentResponse(BaseModel):
    """Schema representing complete document metadata details."""
    id: int
    account_id: int
    original_filename: str
    stored_filename: str
    file_extension: str
    mime_type: str
    file_size: int
    storage_path: str
    checksum: str
    status: DocumentStatus
    chunks_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentPreviewResponse(BaseModel):
    """Schema representing document parsing analytics and text preview snippet."""
    filename: str
    page_count: int | None
    total_chunks: int
    preview_content: str

class DocumentEmbeddingStatusResponse(BaseModel):
    """Schema representing document embedding generation progress and overall state."""
    document_id: int
    status: str
    total_chunks: int
    indexed_chunks: int
    failed_chunks: int

class DocumentStatisticsResponse(BaseModel):
    """Schema representing document vector indexing metrics."""
    total_chunks: int
    indexed_chunks: int
    failed_chunks: int
    embedding_model: str
    indexing_duration: float | None
    vector_collection: str
