import structlog
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message, MessageRole

logger = structlog.get_logger("aegis.storage")

class ConversationRepository:
    """Manages database access layer operations for dialogue sessions and message logs with workspace isolation."""
    
    @staticmethod
    async def create_conversation(db: AsyncSession, account_id: int, workspace_id: int = 1, title: str = "New Conversation") -> Conversation:
        """Saves a new conversation record in PostgreSQL scoped to a workspace."""
        conv = Conversation(account_id=account_id, workspace_id=workspace_id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        logger.info("Conversation Created", conversation_id=conv.id, title=title, workspace_id=workspace_id)
        return conv
        
    @staticmethod
    async def get_conversation(db: AsyncSession, id: int, account_id: int, workspace_id: int = 1) -> Optional[Conversation]:
        """Loads a conversation checking account ownership and workspace isolation."""
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == id, 
                Conversation.account_id == account_id,
                Conversation.workspace_id == workspace_id
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            logger.info("Conversation Loaded", conversation_id=id, workspace_id=workspace_id)
        return conv
        
    @staticmethod
    async def list_conversations(db: AsyncSession, account_id: int, workspace_id: int = 1) -> List[Conversation]:
        """Loads all conversations owned by the account in a specific workspace sorted by updated_at descending."""
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.account_id == account_id,
                Conversation.workspace_id == workspace_id
            )
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())
        
    @staticmethod
    async def rename_conversation(db: AsyncSession, id: int, account_id: int, workspace_id: int = 1, title: str = "") -> Optional[Conversation]:
        """Updates the conversation title after verifying ownership and workspace constraints."""
        conv = await ConversationRepository.get_conversation(db, id, account_id, workspace_id)
        if not conv:
            return None
        conv.title = title
        await db.commit()
        await db.refresh(conv)
        logger.info("Conversation Saved", conversation_id=id, title=title)
        return conv
        
    @staticmethod
    async def delete_conversation(db: AsyncSession, id: int, account_id: int, workspace_id: int = 1) -> bool:
        """Deletes conversation and cascading child messages after verifying ownership and workspace constraints."""
        conv = await ConversationRepository.get_conversation(db, id, account_id, workspace_id)
        if not conv:
            return False
        await db.delete(conv)
        await db.commit()
        logger.info("conversation_deleted", conversation_id=id)
        return True
        
    @staticmethod
    async def create_message(db: AsyncSession, conversation_id: int, account_id: int, workspace_id: int = 1, role: MessageRole = MessageRole.USER, content: str = "") -> Message:
        """Appends and commits a dialog message entry verifying workspace scope and ownership."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.account_id == account_id,
            Conversation.workspace_id == workspace_id
        )
        res = await db.execute(stmt)
        conv = res.scalar_one_or_none()
        if not conv:
            logger.warn("unauthorized_message_creation_blocked", conversation_id=conversation_id, account_id=account_id, workspace_id=workspace_id)
            raise PermissionError("Access Denied: You do not own this conversation or it belongs to another workspace.")
            
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        db.add(msg)
        
        from datetime import datetime, timezone
        conv.updated_at = datetime.now(timezone.utc)
            
        await db.commit()
        await db.refresh(msg)
        logger.info("Message turn persisted", message_id=msg.id, role=role)
        return msg
        
    @staticmethod
    async def get_messages(db: AsyncSession, conversation_id: int, account_id: int, workspace_id: int = 1) -> List[Message]:
        """Loads message history ordered chronologically verifying workspace scope and ownership."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.account_id == account_id,
            Conversation.workspace_id == workspace_id
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            logger.warn("unauthorized_history_access_blocked", conversation_id=conversation_id, account_id=account_id, workspace_id=workspace_id)
            raise PermissionError("Access Denied: You do not own this conversation or it belongs to another workspace.")
            
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
        )
        messages = list(result.scalars().all())
        logger.info("History Loaded", conversation_id=conversation_id, count=len(messages))
        return messages
