import os
import structlog
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.documents.loaders.pdf_loader import PDFLoader
from app.documents.loaders.docx_loader import DocxLoader
from app.documents.loaders.txt_loader import TxtLoader
from app.documents.cleaners.text_cleaner import TextCleaner
from app.documents.chunkers.recursive_chunker import RecursiveChunker

logger = structlog.get_logger("aegis.parsing")

class ParsingService:
    """Service layer coordinating loading, cleaning, chunking, and database persistence."""
    
    @staticmethod
    def get_loader(extension: str):
        """Resolves file extension to a valid Document Loader subclass."""
        ext = extension.lower()
        if ext == "pdf":
            return PDFLoader()
        elif ext == "docx":
            return DocxLoader()
        elif ext in ["txt", "text"]:
            return TxtLoader()
        else:
            raise ValueError(f"Unsupported loader mapping target extension: .{extension}")

    @staticmethod
    async def process_document_by_id(document_id: int) -> None:
        """Executes full parsing, cleaning, chunking, and db commit pipeline for a document."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document:
                logger.error("parsing_failed_not_found", document_id=document_id)
                return

            try:
                # 1. Update status to PROCESSING
                document.status = DocumentStatus.PROCESSING
                await db.commit()
                logger.info("Document Loaded", document_id=document_id, filename=document.original_filename)

                # 2. Resolve loader and extract raw texts
                loader = ParsingService.get_loader(document.file_extension)
                pages = loader.load(document.storage_path)
                logger.info("Text Extracted", document_id=document_id, pages_count=len(pages))

                # 3. Clean and split page texts recursively
                cleaner = TextCleaner()
                chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
                
                chunks_to_create = []
                chunk_index = 0
                
                logger.info("Cleaning Complete", document_id=document_id)
                logger.info("Chunking Started", document_id=document_id)

                for page_text, page_num in pages:
                    cleaned_text = cleaner.clean(page_text)
                    page_chunks = chunker.split_text(cleaned_text)
                    
                    for content in page_chunks:
                        chunk = DocumentChunk(
                            document_id=document_id,
                            chunk_index=chunk_index,
                            page_number=page_num,
                            content=content,
                            character_count=len(content)
                        )
                        chunks_to_create.append(chunk)
                        chunk_index += 1

                logger.info("Chunking Finished", document_id=document_id, total_chunks=len(chunks_to_create))

                # 4. Save chunks to Database
                if chunks_to_create:
                    db.add_all(chunks_to_create)
                
                # 5. Mark document as PROCESSED
                document.status = DocumentStatus.PROCESSED
                await db.commit()
                
                logger.info("Chunks Stored", document_id=document_id, count=len(chunks_to_create))
                logger.info("Document Processed", document_id=document_id)
                
            except Exception as exc:
                logger.error("Document Failed", document_id=document_id, error=str(exc))
                # Set status to FAILED in database
                try:
                    document.status = DocumentStatus.FAILED
                    await db.commit()
                except Exception as inner_exc:
                    logger.error("failed_to_commit_failed_status", error=str(inner_exc))
                raise exc
