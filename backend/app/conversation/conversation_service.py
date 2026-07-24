import structlog
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.storage.conversation_repository import ConversationRepository
from app.conversation.memory_service import MemoryService
from app.conversation.query_rewriter import QueryRewriter

logger = structlog.get_logger("aegis.conversation")

class ConversationService:
    """Orchestrates query rewriting and layered memory summaries."""
    
    @staticmethod
    async def prepare_context(
        db: AsyncSession, 
        conversation: Conversation, 
        question: str, 
        max_history: int = 8
    ) -> Dict[str, Any]:
        """Loads dialogue turns, checks constraints, and rewrites follow-up questions."""
        logger.info("Conversation Loaded", conversation_id=conversation.id)
        
        # Load complete history
        history = await ConversationRepository.get_messages(db, conversation.id, conversation.account_id, conversation.workspace_id)
        
        # Slices history and builds/saves summaries
        summary, active_history = await MemoryService.manage_memory(db, conversation, history, max_history)
        
        # Rewrite contextual follow-up query to standalone query
        rewritten_query = QueryRewriter.rewrite_query(active_history, question)
        
        return {
            "conversation_id": conversation.id,
            "original_query": question,
            "rewritten_query": rewritten_query,
            "summary": summary,
            "active_history": active_history
        }
