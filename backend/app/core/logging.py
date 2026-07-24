import logging
import sys
import structlog

def setup_logging():
    # Redirect standard logging to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Disable standard logging handlers that duplicate messages
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).handlers = []
        logging.getLogger(uvicorn_logger).propagate = True

    from app.observability.logging import observability_processor

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            observability_processor,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Expose specialized loggers
app_logger = structlog.get_logger("aegis.app")
request_logger = structlog.get_logger("aegis.request")
error_logger = structlog.get_logger("aegis.error")
startup_logger = structlog.get_logger("aegis.startup")
db_logger = structlog.get_logger("aegis.database")
