import os
import uuid
import hashlib
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy import func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk, ChunkEmbeddingStatus
from app.schemas.document import (
    DocumentResponse, 
    DocumentPreviewResponse, 
    DocumentEmbeddingStatusResponse, 
    DocumentStatisticsResponse
)
from app.schemas.document_chunk import DocumentChunkResponse
from app.config.settings import settings
from app.core.logging import app_logger
from app.workers.tasks import process_document
from app.security.permissions import PermissionChecker
from app.audit.audit_service import AuditService
from app.tenancy.tenant_context import TenantContext
from app.tenancy.tenant_guard import get_tenant_context, WorkspacePermissionChecker
from app.vectorstore.vector_service import VectorService

router = APIRouter()

UPLOAD_DIR = os.path.join("app", "storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("document:upload"))
) -> Document:
    """
    Receives document uploads (PDF, DOCX, TXT), validates sizes/types, 
    scopes them to the active workspace, and queues background Celery processing.
    """
    filename = file.filename
    if not filename:
        app_logger.error("upload_failed_missing_filename")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing"
        )
        
    app_logger.info("upload_started", filename=filename, account_id=current_account.id, workspace_id=tenant_context.workspace.id)
    
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        app_logger.warn("upload_failed_invalid_extension", filename=filename, extension=ext)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: .{ext}. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    allowed_mimes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    if file.content_type not in allowed_mimes:
        app_logger.warn("upload_failed_invalid_mime", filename=filename, mime=file.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type: {file.content_type}. Allowed: PDF, DOCX, TXT"
        )

    file_size = file.size
    if file_size is None:
        content = await file.read()
        file_size = len(content)
        await file.seek(0)
    
    if file_size == 0:
        app_logger.warn("upload_failed_empty_file", filename=filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
        
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        app_logger.warn("upload_failed_file_too_large", filename=filename, size=file_size)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    stored_name = f"{uuid.uuid4()}.{ext}"
    storage_path = os.path.join(UPLOAD_DIR, stored_name)

    try:
        file_content = await file.read()
        checksum = hashlib.sha256(file_content).hexdigest()
        
        with open(storage_path, "wb") as f:
            f.write(file_content)
    except Exception as exc:
        app_logger.error("upload_failed_storage_write", filename=filename, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write document to storage"
        )
    finally:
        await file.close()

    db_doc = Document(
        account_id=current_account.id,
        workspace_id=tenant_context.workspace.id,
        original_filename=filename,
        stored_filename=stored_name,
        file_extension=ext,
        mime_type=file.content_type,
        file_size=file_size,
        storage_path=storage_path,
        checksum=checksum,
        status=DocumentStatus.UPLOADED
    )
    
    try:
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
    except Exception as exc:
        app_logger.error("upload_failed_metadata_commit", filename=filename, error=str(exc))
        if os.path.exists(storage_path):
            os.remove(storage_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register document metadata"
        )

    app_logger.info("upload_completed", filename=filename, document_id=db_doc.id)

    try:
        process_document.delay(db_doc.id)
        app_logger.info("celery_task_queued", document_id=db_doc.id)
        
        db_doc.status = DocumentStatus.QUEUED
        await db.commit()
        await db.refresh(db_doc)
    except Exception as exc:
        app_logger.error("celery_queue_failed", document_id=db_doc.id, error=str(exc))

    await AuditService.log_event(
        db=db,
        account_id=current_account.id,
        workspace_id=tenant_context.workspace.id,
        action="DOCUMENT_UPLOAD",
        resource="document",
        resource_id=str(db_doc.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata_json={"filename": db_doc.original_filename}
    )
        
    return db_doc

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> List[Document]:
    """Lists all knowledge base documents belonging to the active workspace."""
    result = await db.execute(
        select(Document)
        .where(Document.workspace_id == tenant_context.workspace.id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())

@router.get("/{id}", response_model=DocumentResponse)
async def read_document(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> Document:
    """Fetches details of a specific document within the active workspace."""
    result = await db.execute(
        select(Document).where(
            Document.id == id, 
            Document.workspace_id == tenant_context.workspace.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )
    return doc

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_document(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("document:delete"))
) -> dict:
    """Deletes a document and its associated vectors from the active workspace."""
    result = await db.execute(
        select(Document).where(
            Document.id == id, 
            Document.workspace_id == tenant_context.workspace.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )

    # 1. Delete physical file
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
            app_logger.info("file_deleted_from_disk", path=doc.storage_path)
        except Exception as exc:
            app_logger.error("file_deletion_failed", path=doc.storage_path, error=str(exc))

    # 2. Delete vectors from ChromaDB
    try:
        VectorService.delete_document_vectors(doc.id, collection_name=f"workspace_{tenant_context.workspace.id}")
        app_logger.info("vectors_deleted_from_chromadb", document_id=id, workspace_id=tenant_context.workspace.id)
    except Exception as exc:
        app_logger.error("vector_deletion_failed", document_id=id, error=str(exc))

    # 3. Delete metadata record
    try:
        filename = doc.original_filename
        await db.delete(doc)
        await db.commit()
        
        # Invalidate search cache for the workspace
        from app.cache.retrieval_cache import RetrievalCache
        await RetrievalCache.invalidate_workspace(tenant_context.workspace.id)
        
        app_logger.info("document_metadata_deleted", document_id=id)

        
        await AuditService.log_event(
            db=db,
            account_id=current_account.id,
            workspace_id=tenant_context.workspace.id,
            action="DOCUMENT_DELETE",
            resource="document",
            resource_id=str(id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata_json={"filename": filename}
        )
    except Exception as exc:
        app_logger.error("metadata_deletion_failed", document_id=id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document metadata record"
        )

    return {
        "success": True,
        "message": "Document successfully deleted"
    }

@router.get("/{id}/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> List[DocumentChunk]:
    """Retrieves all parsed text chunks for a document inside the active workspace."""
    result = await db.execute(
        select(Document).where(
            Document.id == id, 
            Document.workspace_id == tenant_context.workspace.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )
        
    chunks_result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(chunks_result.scalars().all())

@router.get("/{id}/preview", response_model=DocumentPreviewResponse)
async def preview_document(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> dict:
    """Returns snippet preview of the document's parsed text in the active workspace."""
    result = await db.execute(
        select(Document).where(
            Document.id == id, 
            Document.workspace_id == tenant_context.workspace.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )
        
    chunks_count_result = await db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == id)
    )
    total_chunks = chunks_count_result.scalar_one() or 0
    
    max_page_result = await db.execute(
        select(func.max(DocumentChunk.page_number)).where(DocumentChunk.document_id == id)
    )
    max_page = max_page_result.scalar_one()
    page_count = max_page if max_page is not None else 1
    
    first_chunk_result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == id)
        .order_by(DocumentChunk.chunk_index.asc())
        .limit(1)
    )
    first_chunk = first_chunk_result.scalar_one_or_none()
    
    preview_content = first_chunk.content[:500] if first_chunk else "No text chunks generated yet."
    
    return {
        "filename": doc.original_filename,
        "page_count": page_count if doc.file_extension.lower() == "pdf" else 1,
        "total_chunks": total_chunks,
        "preview_content": preview_content
    }

@router.get("/{id}/embedding-status", response_model=DocumentEmbeddingStatusResponse)
async def get_embedding_status(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> dict:
    """Calculates overall embedding status progress for a document in the active workspace."""
    result = await db.execute(
        select(Document).where(
            Document.id == id, 
            Document.workspace_id == tenant_context.workspace.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )
        
    chunks_result = await db.execute(
        select(DocumentChunk.embedding_status, func.count(DocumentChunk.id))
        .where(DocumentChunk.document_id == id)
        .group_by(DocumentChunk.embedding_status)
    )
    counts = {s: c for s, c in chunks_result.all()}
    
    pending = counts.get(ChunkEmbeddingStatus.PENDING, 0)
    processing = counts.get(ChunkEmbeddingStatus.PROCESSING, 0)
    indexed = counts.get(ChunkEmbeddingStatus.INDEXED, 0)
    failed = counts.get(ChunkEmbeddingStatus.FAILED, 0)
    total = pending + processing + indexed + failed
    
    if total == 0:
        overall_status = "PENDING"
    elif indexed == total:
        overall_status = "INDEXED"
    elif failed > 0:
        overall_status = "FAILED"
    elif processing > 0 or indexed > 0:
        overall_status = "PROCESSING"
    else:
        overall_status = "PENDING"
        
    return {
        "document_id": id,
        "status": overall_status,
        "total_chunks": total,
        "indexed_chunks": indexed,
        "failed_chunks": failed
    }

@router.get("/{id}/statistics", response_model=DocumentStatisticsResponse)
async def get_document_statistics(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> dict:
    """Returns vector indexing metrics and processing duration details for a document in the active workspace."""
    result = await db.execute(
        select(Document).where(
            Document.id == id, 
            Document.workspace_id == tenant_context.workspace.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )
        
    chunks_result = await db.execute(
        select(
            func.count(DocumentChunk.id),
            func.sum(case((DocumentChunk.embedding_status == ChunkEmbeddingStatus.INDEXED, 1), else_=0)),
            func.sum(case((DocumentChunk.embedding_status == ChunkEmbeddingStatus.FAILED, 1), else_=0)),
            func.max(DocumentChunk.embedded_at)
        )
        .where(DocumentChunk.document_id == id)
    )
    row = chunks_result.one()
    total_chunks = row[0] or 0
    indexed_chunks = row[1] or 0
    failed_chunks = row[2] or 0
    max_embedded_at = row[3]
    
    indexing_duration = None
    if max_embedded_at and doc.created_at:
        indexing_duration = max(0.0, (max_embedded_at - doc.created_at).total_seconds())
        
    return {
        "total_chunks": total_chunks,
        "indexed_chunks": indexed_chunks,
        "failed_chunks": failed_chunks,
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "indexing_duration": indexing_duration,
        "vector_collection": "documents" if tenant_context.workspace.id == 1 else f"workspace_{tenant_context.workspace.id}"
    }
