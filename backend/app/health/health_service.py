import asyncio
from sqlalchemy import text
from app.database.session import AsyncSessionLocal
from app.utils.redis import check_redis_connection
from app.vectorstore.chroma_client import chroma_client
from app.llm.llm_client import LLMClient
from app.workers.celery import celery_app

class HealthService:
    """Consolidates health checks for core relational, cache, vector, model, and queue systems."""
    
    @staticmethod
    async def check_db() -> bool:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    async def check_redis() -> bool:
        from app.config.settings import settings
        if settings.CELERY_TASK_ALWAYS_EAGER:
            return True
        return await check_redis_connection()

    @staticmethod
    async def check_chromadb() -> bool:
        try:
            # ChromaDB client heartbeat returns integer timestamp if alive
            hb = chroma_client.heartbeat()
            return hb is not None
        except Exception:
            return False

    @staticmethod
    async def check_llm() -> bool:
        try:
            # Verify we can resolve and construct the configured LLM provider
            provider = LLMClient.get_provider()
            return provider is not None
        except Exception:
            return False

    @staticmethod
    async def check_celery() -> bool:
        from app.config.settings import settings
        if settings.CELERY_TASK_ALWAYS_EAGER:
            return True
        try:
            loop = asyncio.get_running_loop()
            # Inspect pings blocking call wrapped in run_in_executor
            inspect = celery_app.control.inspect()
            pings = await loop.run_in_executor(None, inspect.ping)
            return pings is not None and len(pings) > 0
        except Exception:
            # Fallback or offline check
            return False
