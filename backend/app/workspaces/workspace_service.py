from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.config.settings import settings
from app.audit.audit_service import AuditService

class WorkspaceService:
    """
    Handles workspace lifecycle and quota enforcements.
    """
    @staticmethod
    async def create_workspace(
        db: AsyncSession,
        organization_id: int,
        name: str,
        description: str | None,
        creator_id: int,
        ip_address: str = None,
        user_agent: str = None
    ) -> Workspace:
        """
        Creates a workspace if organization limits allow,
        adds creator as OWNER, and logs an audit trail.
        """
        limit = getattr(settings, "MAX_WORKSPACES_PER_ORGANIZATION", 10)
        stmt_count = select(func.count(Workspace.id)).where(Workspace.organization_id == organization_id)
        res_count = await db.execute(stmt_count)
        current_count = res_count.scalar() or 0
        
        if current_count >= limit:
            raise ValueError(f"Organization has reached the maximum quota of {limit} workspaces.")
            
        workspace = Workspace(
            organization_id=organization_id,
            name=name,
            description=description
        )
        db.add(workspace)
        await db.commit()
        await db.refresh(workspace)
        
        # Add creator as OWNER member
        member = WorkspaceMember(
            workspace_id=workspace.id,
            account_id=creator_id,
            role="OWNER"
        )
        db.add(member)
        await db.commit()
        
        # Log Workspace Created event
        await AuditService.log_event(
            db=db,
            account_id=creator_id,
            action="WORKSPACE_CREATE",
            resource="workspace",
            resource_id=str(workspace.id),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={"organization_id": organization_id}
        )
        
        return workspace

    @staticmethod
    async def get_workspace(db: AsyncSession, id: int) -> Workspace | None:
        """Retrieves details of a specific workspace."""
        res = await db.execute(select(Workspace).where(Workspace.id == id))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_user_workspaces(db: AsyncSession, organization_id: int, account_id: int) -> list[Workspace]:
        """Lists workspaces in an organization where the user has active membership."""
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.organization_id == organization_id,
                WorkspaceMember.account_id == account_id
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_workspace(db: AsyncSession, id: int, name: str, description: str | None) -> Workspace | None:
        """Updates workspace details."""
        res = await db.execute(select(Workspace).where(Workspace.id == id))
        ws = res.scalar_one_or_none()
        if not ws:
            return None
            
        ws.name = name
        ws.description = description
        await db.commit()
        await db.refresh(ws)
        return ws

    @staticmethod
    async def delete_workspace(db: AsyncSession, id: int, account_id: int) -> bool:
        """Deletes a workspace and records audits."""
        res = await db.execute(select(Workspace).where(Workspace.id == id))
        ws = res.scalar_one_or_none()
        if not ws:
            return False
            
        await db.delete(ws)
        await db.commit()
        
        # Log Workspace Deleted event
        await AuditService.log_event(
            db=db,
            account_id=account_id,
            action="WORKSPACE_DELETE",
            resource="workspace",
            resource_id=str(id)
        )
        return True
