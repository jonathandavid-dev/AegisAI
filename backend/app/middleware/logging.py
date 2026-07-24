import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import request_logger
from app.observability.logging import bind_observability_fields, clear_observability_fields
from app.observability.metrics import track_request, track_request_duration

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware intercepts HTTP requests to bind correlation IDs,
    log completion statuses, and track latency metrics.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        # Resolve correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Try to resolve workspace from header
        workspace_id = None
        workspace_header = request.headers.get("X-Workspace-ID")
        if workspace_header:
            try:
                workspace_id = int(workspace_header)
            except ValueError:
                pass
                
        # Bind log context variables
        bind_observability_fields(
            correlation_id=correlation_id,
            request_path=request.url.path,
            workspace_id=workspace_id
        )
        
        client_ip = request.client.host if request.client else "unknown"
        request_logger.info(
            "http_request_received",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip
        )
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Update log context with final duration
            bind_observability_fields(duration_ms=duration_ms)
            
            # Prometheus tracking
            track_request(request.method, request.url.path, response.status_code)
            track_request_duration(request.method, request.url.path, duration)
            
            request_logger.info(
                "http_request_processed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            return response
            
        except Exception as exc:
            duration = time.perf_counter() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Update log context with duration and trace error
            bind_observability_fields(duration_ms=duration_ms)
            
            track_request(request.method, request.url.path, 500)
            track_request_duration(request.method, request.url.path, duration)
            
            request_logger.error(
                "http_request_exception",
                method=request.method,
                path=request.url.path,
                exception=exc.__class__.__name__,
                detail=str(exc),
                duration_ms=duration_ms
            )
            raise exc
        finally:
            # Clear context variables to prevent bleed over
            clear_observability_fields()
