from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge
from sqlalchemy import text
from app.database.session import AsyncSessionLocal
from app.config.settings import settings
import structlog

logger = structlog.get_logger("aegis.metrics")

# Prometheus Metrics Definitions
http_requests_total = Counter("http_requests_total", "Total HTTP requests count", ["method", "path", "status"])
http_request_duration_seconds = Histogram("http_request_duration_seconds", "HTTP request processing duration", ["method", "path"])
search_latency_seconds = Histogram("search_latency_seconds", "Vector search retrieval latency")
embedding_latency_seconds = Histogram("embedding_latency_seconds", "Embedding generation latency")
streaming_duration_seconds = Histogram("streaming_duration_seconds", "SSE chat stream duration")
tool_executions_total = Counter("tool_executions_total", "Total tool executions", ["tool_name", "status"])
cache_requests_total = Counter("cache_requests_total", "Total cache requests count", ["cache_type", "status"])

workspaces_total = Gauge("workspaces_total", "Total workspaces count")
documents_total = Gauge("documents_total", "Total documents count")
conversations_total = Gauge("conversations_total", "Total conversations count")

def track_request(method: str, path: str, status: int) -> None:
    if settings.ENABLE_PROMETHEUS:
        http_requests_total.labels(method=method, path=path, status=str(status)).inc()

def track_request_duration(method: str, path: str, duration: float) -> None:
    """Tracks HTTP request duration in seconds."""
    if settings.ENABLE_PROMETHEUS:
        http_request_duration_seconds.labels(method=method, path=path).observe(duration)

def track_search_latency(duration_seconds: float) -> None:
    if settings.ENABLE_PROMETHEUS:
        search_latency_seconds.observe(duration_seconds)

def track_embedding_latency(duration_seconds: float) -> None:
    if settings.ENABLE_PROMETHEUS:
        embedding_latency_seconds.observe(duration_seconds)

def track_streaming_duration(duration_seconds: float) -> None:
    if settings.ENABLE_PROMETHEUS:
        streaming_duration_seconds.observe(duration_seconds)

def track_tool_execution(tool_name: str, status: str) -> None:
    if settings.ENABLE_PROMETHEUS:
        tool_executions_total.labels(tool_name=tool_name, status=status).inc()

def increment_cache_request(cache_type: str, is_hit: bool) -> None:
    if settings.ENABLE_PROMETHEUS:
        status = "hit" if is_hit else "miss"
        cache_requests_total.labels(cache_type=cache_type, status=status).inc()

async def update_db_metrics() -> None:
    """Queries backend PostgreSQL database to populate Gauge metrics."""
    if not settings.ENABLE_PROMETHEUS:
        return
    try:
        async with AsyncSessionLocal() as session:
            # Count workspaces
            res_ws = await session.execute(text("SELECT COUNT(*) FROM workspaces"))
            workspaces_total.set(res_ws.scalar() or 0)
            
            # Count documents
            res_doc = await session.execute(text("SELECT COUNT(*) FROM documents"))
            documents_total.set(res_doc.scalar() or 0)
            
            # Count conversations
            res_conv = await session.execute(text("SELECT COUNT(*) FROM conversations"))
            conversations_total.set(res_conv.scalar() or 0)
    except Exception as e:
        logger.error("failed_to_update_db_metrics", error=str(e))

async def export_metrics() -> tuple[bytes, str]:
    """Generates and returns latest registry state."""
    await update_db_metrics()
    return generate_latest(), CONTENT_TYPE_LATEST
