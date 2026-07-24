from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.schemas.workspace import (
    WorkspaceCreate, 
    WorkspaceResponse, 
    WorkspaceMemberResponse, 
    MemberRoleUpdate, 
    WorkspaceInviteCreate, 
    WorkspaceInviteResponse
)
from app.workspaces.workspace_service import WorkspaceService
from app.workspaces.membership_service import MembershipService
from app.organizations.invitation_service import InvitationService
from app.organizations.organization_service import OrganizationService
from app.tenancy.tenant_context import TenantContext
from app.tenancy.tenant_guard import get_tenant_context, WorkspacePermissionChecker

router = APIRouter()

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: Request,
    organization_id: int,
    body: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> WorkspaceResponse:
    """Creates a new workspace inside an organization."""
    # Verify user belongs to organization
    orgs = await OrganizationService.list_user_organizations(db, current_account.id)
    if organization_id not in [o.id for o in orgs]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not belong to this organization.")
        
    try:
        ws = await WorkspaceService.create_workspace(
            db=db,
            organization_id=organization_id,
            name=body.name,
            description=body.description,
            creator_id=current_account.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return ws
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> List[WorkspaceResponse]:
    """Lists workspaces in an organization where the user has active membership."""
    return await WorkspaceService.list_user_workspaces(db, organization_id, current_account.id)

@router.get("/{id}", response_model=WorkspaceResponse)
async def get_workspace(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> WorkspaceResponse:
    """Gets details of a workspace (active member only)."""
    return tenant_context.workspace

@router.patch("/{id}", response_model=WorkspaceResponse)
async def update_workspace(
    id: int,
    body: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:write"))
) -> WorkspaceResponse:
    """Updates workspace details."""
    ws = await WorkspaceService.update_workspace(db, id, body.name, body.description)
    return ws

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_workspace(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:delete"))
) -> dict:
    """Deletes workspace and cascading child resources."""
    success = await WorkspaceService.delete_workspace(db, id, current_account.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    
    # Invalidate both search and embedding caches for the workspace
    from app.cache.retrieval_cache import RetrievalCache
    from app.cache.embedding_cache import EmbeddingCache
    await RetrievalCache.invalidate_workspace(id)
    await EmbeddingCache.invalidate_workspace(id)
    
    return {"success": True, "message": "Workspace deleted successfully."}


# MEMBERS ENDPOINTS

@router.get("/{id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> list:
    """Lists active workspace members alongside account details."""
    return await MembershipService.list_members(db, id)

@router.post("/{id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    id: int,
    account_id: int,
    body: MemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:write"))
) -> WorkspaceMemberResponse:
    """Enrolls an account as a member of the workspace."""
    try:
        member = await MembershipService.add_member(
            db=db,
            workspace_id=id,
            account_id=account_id,
            role=body.role,
            actor_id=current_account.id
        )
        return member
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.delete("/{id}/members/{account_id}", status_code=status.HTTP_200_OK)
async def remove_workspace_member(
    id: int,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:write"))
) -> dict:
    """Removes a member from the workspace."""
    try:
        success = await MembershipService.remove_member(db, id, account_id, current_account.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
        return {"success": True, "message": "Member removed successfully."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.patch("/{id}/members/{account_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member_role(
    id: int,
    account_id: int,
    body: MemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:write"))
) -> WorkspaceMemberResponse:
    """Promotes or demotes user workspace role permissions."""
    try:
        member = await MembershipService.update_member_role(
            db=db,
            workspace_id=id,
            account_id=account_id,
            new_role=body.role,
            actor_id=current_account.id
        )
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
        return member
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

# INVITATIONS ENDPOINTS

@router.post("/{id}/invitations", response_model=WorkspaceInviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_workspace_member(
    id: int,
    body: WorkspaceInviteCreate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:invite"))
) -> WorkspaceInviteResponse:
    """Sends invitation to join a workspace."""
    invite = await InvitationService.invite_member(
        db=db,
        workspace_id=id,
        email=body.email,
        invited_by=current_account.id
    )
    return invite

@router.get("/{id}/invitations", response_model=List[WorkspaceInviteResponse])
async def list_pending_workspace_invitations(
    id: int,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(WorkspacePermissionChecker("workspace:read"))
) -> List[WorkspaceInviteResponse]:
    """Lists pending workspace invitations."""
    return await InvitationService.list_pending_invitations(db, id)

@router.post("/invitations/{invitation_id}/accept", status_code=status.HTTP_200_OK)
async def accept_workspace_invitation(
    invitation_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> dict:
    """Accepts a pending workspace invitation."""
    try:
        success = await InvitationService.accept_invitation(db, invitation_id, current_account.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is invalid, expired, or already accepted.")
        return {"success": True, "message": "Invitation accepted. Workspace access granted."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.post("/invitations/{invitation_id}/decline", status_code=status.HTTP_200_OK)
async def decline_workspace_invitation(
    invitation_id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> dict:
    """Declines a pending workspace invitation."""
    try:
        success = await InvitationService.decline_invitation(db, invitation_id, current_account.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is invalid or already processed.")
        return {"success": True, "message": "Invitation declined."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
