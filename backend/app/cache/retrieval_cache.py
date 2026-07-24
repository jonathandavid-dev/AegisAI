import hashlib
import json
from typing import Any, Optional
from app.cache.cache_service import CacheService

class RetrievalCache:
    """Workspace-aware search/retrieval result caching layer."""

    @staticmethod
    def _make_key(workspace_id: int, query: str, top_k: int, filters: Any) -> str:
        # Generate a unique stable hash for query + top_k + filters combination
        raw_key = f"q:{query.strip()}|k:{top_k}|f:{json.dumps(filters or {}, sort_keys=True)}"
        hashed = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        return f"workspace:{workspace_id}:search:{hashed}"

    @classmethod
    async def get(cls, workspace_id: int, query: str, top_k: int, filters: Any) -> Optional[dict]:
        key = cls._make_key(workspace_id, query, top_k, filters)
        result = await CacheService.get(key)
        
        # Track metrics (lazy import to prevent circular dependency)
        try:
            from app.observability.metrics import increment_cache_request
            if result is not None:
                increment_cache_request("retrieval", is_hit=True)
            else:
                increment_cache_request("retrieval", is_hit=False)
        except Exception:
            pass
            
        return result

    @classmethod
    async def set(cls, workspace_id: int, query: str, top_k: int, filters: Any, value: dict) -> None:
        key = cls._make_key(workspace_id, query, top_k, filters)
        await CacheService.set(key, value)

    @classmethod
    async def invalidate_workspace(cls, workspace_id: int) -> None:
        """Invalidates all cached search results for a specific workspace."""
        pattern = f"workspace:{workspace_id}:search:*"
        await CacheService.invalidate_pattern(pattern)
