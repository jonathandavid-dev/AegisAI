import redis.asyncio as redis
from app.config.settings import settings
from app.core.logging import app_logger

async def check_redis_connection() -> bool:
    """Pings the Redis host using settings configuration variables."""
    client = None
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            socket_timeout=2
        )
        await client.ping()
        return True
    except Exception as exc:
        app_logger.error("redis_connection_failed", error=str(exc))
        return False
    finally:
        if client:
            await client.close()
