from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace_member import WorkspaceMember
from app.models.account import Account
from app.config.settings import settings
from app.audit.audit_service import AuditService

class MembershipService:
    """
    Manages workspace membership listing, additions, and updates.
    """
    @staticmethod
    async def add_member(
        db: AsyncSession, 
        workspace_id: int, 
        account_id: int, 
        role: str,
        actor_id: int
    ) -> WorkspaceMember:
        """
        Adds a new account as a member of the workspace, checking membership limit.
        """
        limit = getattr(settings, "MAX_MEMBERS_PER_WORKSPACE", 50)
        stmt_count = select(func.count(WorkspaceMember.id)).where(WorkspaceMember.workspace_id == workspace_id)
        res_count = await db.execute(stmt_count)
        current_count = res_count.scalar() or 0
        
        if current_count >= limit:
            raise ValueError(f"Workspace has reached the maximum allowed limit of {limit} members.")
            
        stmt_check = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.account_id == account_id
        )
        res_check = await db.execute(stmt_check)
        if res_check.scalar_one_or_none():
            raise ValueError("Account is already enrolled as a member of this workspace.")
            
        member = WorkspaceMember(
            workspace_id=workspace_id,
            account_id=account_id,
            role=role.upper()
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        
        # Log member added event
        await AuditService.log_event(
            db=db,
            account_id=actor_id,
            action="WORKSPACE_MEMBER_ADD",
            resource="workspace",
            resource_id=str(workspace_id),
            metadata_json={"added_account_id": account_id, "role": role}
        )
        
        return member

    @staticmethod
    async def remove_member(db: AsyncSession, workspace_id: int, account_id: int, actor_id: int) -> bool:
        """
        Removes a member from the workspace, keeping at least one OWNER.
        """
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.account_id == account_id
        )
        res = await db.execute(stmt)
        member = res.scalar_one_or_none()
        
        if not member:
            return False
            
        if member.role == "OWNER":
            stmt_owners = select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "OWNER"
            )
            res_owners = await db.execute(stmt_owners)
            owners_count = res_owners.scalar() or 0
            if owners_count <= 1:
                raise ValueError("Cannot remove member: Workspaces must contain at least one OWNER.")
                
        await db.delete(member)
        await db.commit()
        
        # Log member removed event
        await AuditService.log_event(
            db=db,
            account_id=actor_id,
            action="MEMBER_REMOVE",
            resource="workspace",
            resource_id=str(workspace_id),
            metadata_json={"removed_account_id": account_id}
        )
        return True

    @staticmethod
    async def update_member_role(
        db: AsyncSession, 
        workspace_id: int, 
        account_id: int, 
        new_role: str,
        actor_id: int
    ) -> WorkspaceMember | None:
        """Promotes or demotes user workspace role permissions."""
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.account_id == account_id
        )
        res = await db.execute(stmt)
        member = res.scalar_one_or_none()
        
        if not member:
            return None
            
        if member.role == "OWNER" and new_role.upper() != "OWNER":
            stmt_owners = select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "OWNER"
            )
            res_owners = await db.execute(stmt_owners)
            owners_count = res_owners.scalar() or 0
            if owners_count <= 1:
                raise ValueError("Cannot demote OWNER: Workspaces must contain at least one active OWNER.")
                
        member.role = new_role.upper()
        await db.commit()
        await db.refresh(member)
        
        # Log role changed event
        await AuditService.log_event(
            db=db,
            account_id=actor_id,
            action="WORKSPACE_MEMBER_ROLE_UPDATE",
            resource="workspace",
            resource_id=str(workspace_id),
            metadata_json={"account_id": account_id, "new_role": new_role}
        )
        return member

    @staticmethod
    async def list_members(db: AsyncSession, workspace_id: int) -> list[dict]:
        """Lists active workspace members alongside account details."""
        stmt = (
            select(WorkspaceMember, Account)
            .join(Account, Account.id == WorkspaceMember.account_id)
            .where(WorkspaceMember.workspace_id == workspace_id)
        )
        res = await db.execute(stmt)
        members_list = []
        for row in res.all():
            member, acc = row
            members_list.append({
                "account_id": acc.id,
                "username": acc.username,
                "email": acc.email,
                "full_name": acc.full_name,
                "role": member.role,
                "joined_at": member.joined_at
            })
        return members_list
