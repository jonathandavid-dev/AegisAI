import structlog
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk, ChunkEmbeddingStatus
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.vector_service import VectorService

logger = structlog.get_logger("aegis.indexing")

class IndexingService:
    """Orchestrates loading chunks, generating vector embeddings, and saving to ChromaDB."""
    
    @staticmethod
    async def index_document(document_id: int, batch_size: int = 32) -> None:
        """Runs the vector indexing workflow for all pending chunks of a document."""
        async with AsyncSessionLocal() as db:
            # 1. Verify document existence
            doc_result = await db.execute(select(Document).where(Document.id == document_id))
            document = doc_result.scalar_one_or_none()
            if not document:
                logger.error("indexing_failed_not_found", document_id=document_id)
                return

            # 2. Fetch pending or failed chunks
            chunks_result = await db.execute(
                select(DocumentChunk)
                .where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.embedding_status.in_([
                        ChunkEmbeddingStatus.PENDING, 
                        ChunkEmbeddingStatus.FAILED
                    ])
                )
                .order_by(DocumentChunk.chunk_index.asc())
            )
            chunks = list(chunks_result.scalars().all())
            if not chunks:
                logger.info("no_chunks_require_indexing", document_id=document_id)
                return

            try:
                # 3. Transition status to PROCESSING
                for chunk in chunks:
                    chunk.embedding_status = ChunkEmbeddingStatus.PROCESSING
                await db.commit()

                # 4. Generate embeddings
                texts = [chunk.content for chunk in chunks]
                embeddings = EmbeddingService.embed_texts(texts, batch_size=batch_size)

                # 5. Populate Chroma schema inputs
                ids = [f"doc_{document_id}_chunk_{chunk.chunk_index}" for chunk in chunks]
                metadatas = [
                    {
                        "document_id": document_id,
                        "filename": document.original_filename,
                        "page_number": chunk.page_number if chunk.page_number is not None else 1,
                        "chunk_index": chunk.chunk_index,
                        "checksum": document.checksum,
                        "created_at": document.created_at.isoformat() if document.created_at else datetime.now(timezone.utc).isoformat()
                    }
                    for chunk in chunks
                ]

                # 6. Save vectors in ChromaDB (scoped by workspace collection)
                VectorService.upsert_chunks(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    collection_name=f"workspace_{document.workspace_id}"
                )

                # 7. Update status to INDEXED
                now = datetime.now(timezone.utc)
                for chunk in chunks:
                    chunk.embedding_status = ChunkEmbeddingStatus.INDEXED
                    chunk.embedded_at = now
                await db.commit()

                # Invalidate search cache for the workspace
                from app.cache.retrieval_cache import RetrievalCache
                await RetrievalCache.invalidate_workspace(document.workspace_id)

                logger.info("Indexing Complete", document_id=document_id, count=len(chunks))



            except Exception as exc:
                logger.error("Indexing Failed", document_id=document_id, error=str(exc))
                # Set status to FAILED in database
                try:
                    for chunk in chunks:
                        chunk.embedding_status = ChunkEmbeddingStatus.FAILED
                    await db.commit()
                except Exception as inner_exc:
                    logger.error("failed_to_commit_failed_indexing", error=str(inner_exc))
                raise exc
