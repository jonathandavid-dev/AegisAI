import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.storage.conversation_repository import ConversationRepository

logger = structlog.get_logger("aegis.chat")

class SessionManager:
    """Encapsulates session creation or validation boundaries with workspace isolation."""
    
    @staticmethod
    async def get_or_create_session(
        db: AsyncSession, 
        conversation_id: int | None, 
        account_id: int, 
        workspace_id: int,
        initial_title: str = "New Conversation"
    ) -> Conversation:
        """Retrieves an existing conversation session or initializes a new record scoped to a workspace."""
        if conversation_id is not None:
            conv = await ConversationRepository.get_conversation(db, conversation_id, account_id, workspace_id)
            if conv:
                return conv
                
        conv = await ConversationRepository.create_conversation(db, account_id, workspace_id, title=initial_title)
        from app.audit.audit_service import AuditService
        await AuditService.log_event(
            db=db,
            account_id=account_id,
            workspace_id=workspace_id,
            action="CONVERSATION_CREATE",
            resource="conversation",
            resource_id=str(conv.id)
        )
        return conv
