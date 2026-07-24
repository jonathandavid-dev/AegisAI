from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.core.logging import setup_logging, startup_logger, app_logger
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.exceptions import register_exception_handlers
from app.api.router import router as api_router
from app.database.session import engine
from app.utils.redis import check_redis_connection

# Configure logging before application startup
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup checks (DB ping, Redis connection verification)
    and shutdown actions (engine disposal).
    """
    startup_logger.info("application_startup_initiated", app_name=settings.APP_NAME)
    
    # 1. Verify PostgreSQL Database Connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        startup_logger.info("database_connection_verified")
    except Exception as exc:
        startup_logger.critical("database_connection_failed", error=str(exc))
    
    # 2. Verify Redis Connection
    redis_ok = await check_redis_connection()
    if redis_ok:
        startup_logger.info("redis_connection_verified")
    else:
        startup_logger.critical("redis_connection_failed")
        
    yield
    
    # Shutdown operations
    startup_logger.info("application_shutdown_initiated")
    await engine.dispose()
    startup_logger.info("database_engine_disposed")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Agentic Knowledge Platform API Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Custom logging and middleware
app.add_middleware(RequestLoggingMiddleware)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception mapper
register_exception_handlers(app)

# Register central routers
app.include_router(api_router, prefix="/api")

@app.get("/metrics", tags=["Observability"])
async def metrics_root():
    from app.observability.metrics import export_metrics
    from fastapi import Response
    content, mime = await export_metrics()
    return Response(content=content, media_type=mime)

@app.get("/", tags=["System Root"])
async def read_root() -> dict:
    """Returns application name and operational status."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online"
    }

