import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class ChunkEmbeddingStatus(str, enum.Enum):
    """Execution state representing embedding vector generation lifecycle."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"

class DocumentChunk(Base):
    """
    DocumentChunk model representing semantic parts of an ingested document.
    Maintains relationships with parent Document and tracks embedding status.
    Rich metadata fields enable enterprise-grade RAG citations and filtering.
    """
    __tablename__ = "document_chunks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Rich semantic metadata — populated by SemanticChunker
    section: Mapped[str | None] = mapped_column(String(512), nullable=True)
    heading: Mapped[str | None] = mapped_column(String(512), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)   # comma-separated
    hierarchy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0=doc, 1=section, 2=sub
    chunk_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default="paragraph")
    
    embedding_status: Mapped[ChunkEmbeddingStatus] = mapped_column(
        Enum(ChunkEmbeddingStatus, name="chunk_embedding_status_enum"),
        default=ChunkEmbeddingStatus.PENDING,
        nullable=False,
        index=True
    )
    embedded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")
