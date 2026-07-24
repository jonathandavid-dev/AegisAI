import time
import json
from collections import OrderedDict
from typing import Any, Optional
import redis.asyncio as redis
from app.config.settings import settings
from app.core.logging import app_logger

class InMemoryCache:
    """Fallback in-memory cache with eviction and TTL support."""
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        value, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]

    def delete_pattern(self, pattern: str) -> None:
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in self.cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            if k in self.cache:
                del self.cache[k]

    def clear(self) -> None:
        self.cache.clear()


class CacheService:
    """Application cache interface utilizing Redis with local in-memory fallback."""
    _redis_client: Optional[redis.Redis] = None
    _in_memory_cache: Optional[InMemoryCache] = None
    _initialized = False

    @classmethod
    def get_in_memory(cls) -> InMemoryCache:
        if cls._in_memory_cache is None:
            cls._in_memory_cache = InMemoryCache(
                max_size=settings.MAX_CACHE_SIZE,
                default_ttl=settings.CACHE_TTL_SECONDS
            )
        return cls._in_memory_cache

    @classmethod
    async def get_redis(cls) -> Optional[redis.Redis]:
        if not cls._initialized:
            try:
                cls._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    socket_timeout=2,
                    decode_responses=True
                )
                await cls._redis_client.ping()
                app_logger.info("cache_service_redis_connected")
            except Exception as e:
                app_logger.warn("cache_service_redis_failed_falling_back", error=str(e))
                cls._redis_client = None
            cls._initialized = True
        return cls._redis_client

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                val = await redis_client.get(key)
                if val is not None:
                    return json.loads(val)
                return None
            except Exception as e:
                app_logger.error("redis_get_error", key=key, error=str(e))
        
        return cls.get_in_memory().get(key)

    @classmethod
    async def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                await redis_client.set(key, json.dumps(value), ex=ttl)
                return
            except Exception as e:
                app_logger.error("redis_set_error", key=key, error=str(e))
        
        cls.get_in_memory().set(key, value, ttl)

    @classmethod
    async def invalidate(cls, key: str) -> None:
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                await redis_client.delete(key)
                return
            except Exception as e:
                app_logger.error("redis_delete_error", key=key, error=str(e))
        
        cls.get_in_memory().delete(key)

    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> None:
        redis_client = await cls.get_redis()
        if redis_client:
            try:
                keys = await redis_client.keys(pattern)
                if keys:
                    cleaned_keys = [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys]
                    await redis_client.delete(*cleaned_keys)
                return
            except Exception as e:
                app_logger.error("redis_delete_pattern_error", pattern=pattern, error=str(e))
        
        cls.get_in_memory().delete_pattern(pattern)
