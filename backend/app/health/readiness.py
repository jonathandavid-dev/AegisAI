import asyncio
from typing import Dict, Any, Tuple
from app.health.health_service import HealthService

class ReadinessCheck:
    """Orchestrates comprehensive downstream checks in parallel and returns HTTP status alongside a detail dictionary."""
    
    @staticmethod
    async def check() -> Tuple[bool, Dict[str, Any]]:
        # Run all dependency verification tasks concurrently
        results = await asyncio.gather(
            HealthService.check_db(),
            HealthService.check_redis(),
            HealthService.check_chromadb(),
            HealthService.check_llm(),
            HealthService.check_celery(),
            return_exceptions=True
        )
        
        db_ok = results[0] if not isinstance(results[0], Exception) else False
        redis_ok = results[1] if not isinstance(results[1], Exception) else False
        chromadb_ok = results[2] if not isinstance(results[2], Exception) else False
        llm_ok = results[3] if not isinstance(results[3], Exception) else False
        celery_ok = results[4] if not isinstance(results[4], Exception) else False
        
        overall_ready = all([db_ok, redis_ok, chromadb_ok, llm_ok, celery_ok])
        
        details = {
            "database": "ok" if db_ok else "unreachable",
            "redis": "ok" if redis_ok else "unreachable",
            "chromadb": "ok" if chromadb_ok else "unreachable",
            "llm_provider": "ok" if llm_ok else "unconfigured",
            "background_workers": "ok" if celery_ok else "unreachable"
        }
        
        return overall_ready, details
