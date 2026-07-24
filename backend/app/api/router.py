from fastapi import APIRouter
from app.api.v1.router import router as v1_router

router = APIRouter()

# Expose V1 routes under /v1 prefix
router.include_router(v1_router, prefix="/v1")
