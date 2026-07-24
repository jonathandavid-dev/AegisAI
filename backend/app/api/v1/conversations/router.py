from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.storage.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationResponse, MessageResponse, ConversationTitleUpdate
from app.audit.audit_service import AuditService
from app.tenancy.tenant_context import TenantContext
from app.tenancy.tenant_guard import get_tenant_context, WorkspacePermissionChecker

router = APIRouter()

@router.get("", response_model=List[ConversationResponse], status_code=status.HTTP_200_OK)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> List[ConversationResponse]:
    """Retrieves all dialogue sessions owned by the authenticated account in the active workspace."""
    return await ConversationRepository.list_conversations(db, current_account.id, tenant_context.workspace.id)

@router.get("/{id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def get_conversation(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> ConversationResponse:
    """Retrieves metadata details for a specific conversation session in the active workspace."""
    conv = await ConversationRepository.get_conversation(db, id, current_account.id, tenant_context.workspace.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return conv

@router.patch("/{id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def rename_conversation(
    id: int,
    request: ConversationTitleUpdate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> ConversationResponse:
    """Updates the user title of a conversation session in the active workspace."""
    conv = await ConversationRepository.rename_conversation(db, id, current_account.id, tenant_context.workspace.id, request.title)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return conv

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
    id: int,
    request_http: Request,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> dict:
    """Removes a conversation session and all its child messages inside the active workspace."""
    success = await ConversationRepository.delete_conversation(db, id, current_account.id, tenant_context.workspace.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
        
    await AuditService.log_event(
        db=db,
        account_id=current_account.id,
        workspace_id=tenant_context.workspace.id,
        action="CONVERSATION_DELETE",
        resource="conversation",
        resource_id=str(id),
        ip_address=request_http.client.host if request_http.client else None,
        user_agent=request_http.headers.get("user-agent")
    )
    return {"success": True, "message": "Conversation successfully deleted."}

@router.get("/{id}/messages", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def get_conversation_messages(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> List[MessageResponse]:
    """Retrieves chronological message exchange history for a conversation session in the active workspace."""
    conv = await ConversationRepository.get_conversation(db, id, current_account.id, tenant_context.workspace.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return await ConversationRepository.get_messages(db, id, current_account.id, tenant_context.workspace.id)
