import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.config.settings import settings
from app.audit.audit_service import AuditService

class OrganizationService:
    """
    Handles lifecycle operations for tenant Organizations.
    """
    @staticmethod
    def slugify(text: str) -> str:
        """Utility converting text to a unique URL slug."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text

    @classmethod
    async def create_organization(
        cls, 
        db: AsyncSession, 
        name: str, 
        owner_id: int,
        ip_address: str = None,
        user_agent: str = None
    ) -> Organization:
        """
        Creates a new organization, registers a default workspace,
        sets creator as OWNER, and logs an audit trail.
        """
        slug = cls.slugify(name)
        
        # Verify slug uniqueness
        stmt_check = select(Organization).where(Organization.slug == slug)
        res_check = await db.execute(stmt_check)
        if res_check.scalar_one_or_none():
            import random
            slug = f"{slug}-{random.randint(1000, 9999)}"
            
        org = Organization(name=name, slug=slug, owner_id=owner_id)
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        # Auto-provision Default Workspace
        ws_name = getattr(settings, "DEFAULT_WORKSPACE_NAME", "Personal Workspace")
        default_ws = Workspace(
            organization_id=org.id,
            name=ws_name,
            description=f"Default workspace for {org.name}"
        )
        db.add(default_ws)
        await db.commit()
        await db.refresh(default_ws)
        
        # Auto-add creator as Workspace Owner
        member = WorkspaceMember(
            workspace_id=default_ws.id,
            account_id=owner_id,
            role="OWNER"
        )
        db.add(member)
        await db.commit()
        
        # Log Organization Created event
        await AuditService.log_event(
            db=db,
            account_id=owner_id,
            action="ORGANIZATION_CREATE",
            resource="organization",
            resource_id=str(org.id),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json={"slug": slug, "default_workspace_id": default_ws.id}
        )
        
        return org

    @staticmethod
    async def get_organization(db: AsyncSession, id: int) -> Organization | None:
        """Retrieves details of a specific organization."""
        res = await db.execute(select(Organization).where(Organization.id == id))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_user_organizations(db: AsyncSession, account_id: int) -> list[Organization]:
        """Lists all organizations owned or joined by the user account."""
        stmt = (
            select(Organization)
            .outerjoin(Workspace, Workspace.organization_id == Organization.id)
            .outerjoin(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                (Organization.owner_id == account_id) |
                (WorkspaceMember.account_id == account_id)
            )
            .distinct()
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_organization(db: AsyncSession, id: int, name: str) -> Organization | None:
        """Updates organization details."""
        res = await db.execute(select(Organization).where(Organization.id == id))
        org = res.scalar_one_or_none()
        if not org:
            return None
            
        org.name = name
        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def delete_organization(db: AsyncSession, id: int) -> bool:
        """Deletes an organization and cascades to child workspaces."""
        res = await db.execute(select(Organization).where(Organization.id == id))
        org = res.scalar_one_or_none()
        if not org:
            return False
            
        await db.delete(org)
        await db.commit()
        return True
