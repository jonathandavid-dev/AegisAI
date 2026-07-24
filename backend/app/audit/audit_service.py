import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.audit.audit_repository import AuditRepository

logger = structlog.get_logger("aegis.audit")

class AuditService:
    """Service providing wrapper methods to log security events safely."""
    
    @staticmethod
    async def log_event(
        db: AsyncSession,
        account_id: int | None,
        action: str,
        resource: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata_json: dict | None = None,
        workspace_id: int | None = None
    ) -> None:
        """Saves audit entries into the database and writes structured log statements to stdout."""
        try:
            await AuditRepository.create_audit_log(
                db=db,
                account_id=account_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_json=metadata_json,
                workspace_id=workspace_id
            )
            logger.info(
                "Audit logged",
                account_id=account_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                workspace_id=workspace_id
            )
        except Exception as exc:
            logger.error("Audit logging failed", error=str(exc))
