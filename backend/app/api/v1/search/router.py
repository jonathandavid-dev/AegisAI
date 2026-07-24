from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.schemas.search import SearchRequest, SearchResponse
from app.search.search_service import SearchService
from app.tenancy.tenant_context import TenantContext
from app.tenancy.tenant_guard import get_tenant_context, WorkspacePermissionChecker

router = APIRouter()

@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def perform_search(
    request: SearchRequest,
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> dict:
    """Performs standard semantic vector search scoped to the active workspace."""
    results = await SearchService.search(
        query=request.query,
        workspace_id=tenant_context.workspace.id,
        top_k=request.top_k,
        filters=request.filters,
        similarity_threshold=0.50
    )
    return results

@router.post("/advanced", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def perform_advanced_search(
    request: SearchRequest,
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> dict:
    """Performs advanced semantic search allowing custom score thresholds scoped to the active workspace."""
    threshold = float(request.filters.pop("similarity_threshold", 0.50)) if request.filters else 0.50
    results = await SearchService.search(
        query=request.query,
        workspace_id=tenant_context.workspace.id,
        top_k=request.top_k,
        filters=request.filters,
        similarity_threshold=threshold
    )
    return results

