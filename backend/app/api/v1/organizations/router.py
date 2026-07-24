from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.organizations.organization_service import OrganizationService

router = APIRouter()

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: Request,
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> OrganizationResponse:
    """Creates a new Organization with a default Workspace."""
    return await OrganizationService.create_organization(
        db=db,
        name=body.name,
        owner_id=current_account.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> List[OrganizationResponse]:
    """Lists all organizations owned or joined by the user."""
    return await OrganizationService.list_user_organizations(db, current_account.id)

@router.get("/{id}", response_model=OrganizationResponse)
async def get_organization(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> OrganizationResponse:
    """Gets details of an organization if user is associated with it."""
    org = await OrganizationService.get_organization(db, id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
        
    orgs = await OrganizationService.list_user_organizations(db, current_account.id)
    if org.id not in [o.id for o in orgs]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        
    return org

@router.patch("/{id}", response_model=OrganizationResponse)
async def update_organization(
    id: int,
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> OrganizationResponse:
    """Updates organization name (Owner only)."""
    org = await OrganizationService.get_organization(db, id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
        
    if org.owner_id != current_account.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the organization owner can perform updates.")
        
    updated = await OrganizationService.update_organization(db, id, body.name)
    return updated

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_organization(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
) -> dict:
    """Deletes organization and cascades to workspaces (Owner only)."""
    org = await OrganizationService.get_organization(db, id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
        
    if org.owner_id != current_account.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the organization owner can perform deletion.")
        
    await OrganizationService.delete_organization(db, id)
    return {"success": True, "message": "Organization deleted successfully."}
