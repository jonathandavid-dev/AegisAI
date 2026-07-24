import hashlib
from typing import List, Optional
from app.cache.cache_service import CacheService

class EmbeddingCache:
    """Workspace-aware embedding cache for caching text embeddings."""

    @staticmethod
    def _make_key(workspace_id: int, text: str) -> str:
        # Create a unique sha256 hash for the text chunk
        text_hash = hashlib.sha256(text.strip().encode('utf-8')).hexdigest()
        return f"workspace:{workspace_id}:embedding:{text_hash}"

    @classmethod
    async def get(cls, workspace_id: int, text: str) -> Optional[List[float]]:
        key = cls._make_key(workspace_id, text)
        result = await CacheService.get(key)
        
        # Track metrics (lazy import to avoid circular dependency)
        try:
            from app.observability.metrics import increment_cache_request
            if result is not None:
                increment_cache_request("embedding", is_hit=True)
            else:
                increment_cache_request("embedding", is_hit=False)
        except Exception:
            pass
            
        return result

    @classmethod
    async def set(cls, workspace_id: int, text: str, embedding: List[float]) -> None:
        key = cls._make_key(workspace_id, text)
        await CacheService.set(key, embedding)

    @classmethod
    async def invalidate_workspace(cls, workspace_id: int) -> None:
        """Invalidates all cached embeddings for a workspace."""
        pattern = f"workspace:{workspace_id}:embedding:*"
        await CacheService.invalidate_pattern(pattern)
