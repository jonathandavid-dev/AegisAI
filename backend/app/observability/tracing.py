from contextlib import contextmanager
import structlog
from typing import Generator, Optional, Any
from app.config.settings import settings

logger = structlog.get_logger("aegis.tracing")

_tracer: Optional[Any] = None

def init_tracer() -> None:
    """Initializes standard console OpenTelemetry tracer provider."""
    global _tracer
    if not settings.ENABLE_OPENTELEMETRY:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
        
        provider = TracerProvider()
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("aegis-ai")
        logger.info("opentelemetry_tracer_initialized")
    except Exception as e:
        logger.warn("opentelemetry_tracer_failed_to_initialize", error=str(e))
        _tracer = None

def get_tracer() -> Optional[Any]:
    global _tracer
    if _tracer is None and settings.ENABLE_OPENTELEMETRY:
        init_tracer()
    return _tracer

@contextmanager
def trace_span(span_name: str, attributes: Optional[dict] = None) -> Generator[Optional[Any], None, None]:
    """Provides standard span context boundaries for correlation diagnostics."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
        
    try:
        with tracer.start_as_current_span(span_name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v))
            yield span
    except Exception as exc:
        logger.debug("tracing_span_error", span=span_name, error=str(exc))
        raise exc
