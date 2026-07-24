import asyncio
import time
import structlog
from app.workers.celery import celery_app
from app.documents.services.parsing_service import ParsingService
from app.indexing.indexing_service import IndexingService

logger = structlog.get_logger("aegis.worker")

async def _async_process_document(document_id: int) -> None:
    """Async business execution invoking the ParsingService parsing pipeline."""
    await ParsingService.process_document_by_id(document_id)

async def _async_index_document(document_id: int) -> None:
    """Async business execution invoking the IndexingService embedding pipeline."""
    await IndexingService.index_document(document_id)

@celery_app.task(name="app.workers.tasks.process_document")
def process_document(document_id: int) -> dict:
    """
    Main Celery wrapper task executing async database status 
    transformations inside the worker pool.
    """
    try:
        # Run async engine tasks under standard loop context
        asyncio.run(_async_process_document(document_id))
        # Trigger follow-up embedding indexing
        generate_embeddings.delay(document_id)
        return {"status": "success", "document_id": document_id}
    except Exception as exc:
        logger.error("celery_task_failed", document_id=document_id, error=str(exc))
        return {"status": "failed", "document_id": document_id, "error": str(exc)}

@celery_app.task(name="app.workers.tasks.generate_embeddings")
def generate_embeddings(document_id: int) -> dict:
    """Celery background task performing sentence embedding vector generation."""
    try:
        asyncio.run(_async_index_document(document_id))
        return {"status": "success", "document_id": document_id}
    except Exception as exc:
        logger.error("celery_indexing_failed", document_id=document_id, error=str(exc))
        return {"status": "failed", "document_id": document_id, "error": str(exc)}

@celery_app.task(name="app.workers.tasks.demo_background_task")
def demo_background_task(duration_seconds: int = 5) -> dict:
    """Demo background worker task that logs status, sleeps, and returns."""
    logger.info("background_task_started", duration_seconds=duration_seconds)
    time.sleep(duration_seconds)
    logger.info("background_task_completed", duration_seconds=duration_seconds)
    return {
        "status": "success",
        "task_type": "demo_background_task",
        "processed_seconds": duration_seconds
    }
