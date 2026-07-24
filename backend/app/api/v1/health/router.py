from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response
from app.health.liveness import LivenessCheck
from app.health.readiness import ReadinessCheck
from app.observability.metrics import export_metrics

router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
async def overall_health() -> JSONResponse:
    """Returns general liveness check."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=LivenessCheck.check()
    )

@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_endpoint() -> JSONResponse:
    """Fast liveness probe verification."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=LivenessCheck.check()
    )

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_endpoint() -> JSONResponse:
    """Deep readiness probe checking db, cache, vector index, and worker health."""
    ready, details = await ReadinessCheck.check()
    status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if ready else "not_ready",
            "details": details
        }
    )

@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Exposes Prometheus scrape metrics."""
    content, mime = await export_metrics()
    return Response(content=content, media_type=mime)
