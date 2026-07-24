from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace_invitation import WorkspaceInvitation
from app.models.account import Account
from app.workspaces.membership_service import MembershipService
from app.config.settings import settings
from app.audit.audit_service import AuditService

class InvitationService:
    """
    Manages generation, validation, and acceptance of workspace invitations.
    """
    @staticmethod
    async def invite_member(
        db: AsyncSession,
        workspace_id: int,
        email: str,
        invited_by: int
    ) -> WorkspaceInvitation:
        """
        Creates a new PENDING invitation to join a workspace.
        """
        days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        
        stmt = select(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == email,
            WorkspaceInvitation.status == "PENDING"
        )
        res = await db.execute(stmt)
        invite = res.scalar_one_or_none()
        
        if invite:
            invite.expires_at = expires_at
            invite.invited_by = invited_by
        else:
            invite = WorkspaceInvitation(
                workspace_id=workspace_id,
                email=email,
                invited_by=invited_by,
                status="PENDING",
                expires_at=expires_at
            )
            db.add(invite)
            
        await db.commit()
        await db.refresh(invite)
        
        # Log member invited event
        await AuditService.log_event(
            db=db,
            account_id=invited_by,
            action="MEMBER_INVITED",
            resource="workspace",
            resource_id=str(workspace_id),
            metadata_json={"invited_email": email}
        )
        
        return invite

    @staticmethod
    async def accept_invitation(db: AsyncSession, invitation_id: int, account_id: int) -> bool:
        """
        Processes accepting a pending invitation, adding the user to the workspace.
        """
        res = await db.execute(select(WorkspaceInvitation).where(WorkspaceInvitation.id == invitation_id))
        invite = res.scalar_one_or_none()
        
        if not invite or invite.status != "PENDING":
            return False
            
        if invite.expires_at < datetime.now(timezone.utc):
            invite.status = "EXPIRED"
            await db.commit()
            return False
            
        res_acc = await db.execute(select(Account).where(Account.id == account_id))
        acc = res_acc.scalar_one_or_none()
        if not acc or acc.email.lower() != invite.email.lower():
            raise ValueError("Authenticated account email does not match invitation recipient.")
            
        await MembershipService.add_member(
            db=db,
            workspace_id=invite.workspace_id,
            account_id=account_id,
            role="VIEWER",
            actor_id=account_id
        )
        
        invite.status = "ACCEPTED"
        await db.commit()
        return True

    @staticmethod
    async def decline_invitation(db: AsyncSession, invitation_id: int, account_id: int) -> bool:
        """Declines an active invitation."""
        res = await db.execute(select(WorkspaceInvitation).where(WorkspaceInvitation.id == invitation_id))
        invite = res.scalar_one_or_none()
        
        if not invite or invite.status != "PENDING":
            return False
            
        res_acc = await db.execute(select(Account).where(Account.id == account_id))
        acc = res_acc.scalar_one_or_none()
        if not acc or acc.email.lower() != invite.email.lower():
            raise ValueError("Authenticated account email does not match invitation recipient.")
            
        invite.status = "DECLINED"
        await db.commit()
        return True

    @staticmethod
    async def list_pending_invitations(db: AsyncSession, workspace_id: int) -> list[WorkspaceInvitation]:
        """Lists active pending invitations within a workspace context."""
        stmt = select(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.status == "PENDING"
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
