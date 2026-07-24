from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

class AuditRepository:
    """Repository handling SQL operations to log system audit records."""
    
    @staticmethod
    async def create_audit_log(
        db: AsyncSession,
        account_id: int | None,
        action: str,
        resource: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata_json: dict | None = None,
        workspace_id: int | None = None
    ) -> AuditLog:
        """Creates and persists an AuditLog entry."""
        db_log = AuditLog(
            account_id=account_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata_json,
            workspace_id=workspace_id,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(db_log)
        await db.commit()
        return db_log
