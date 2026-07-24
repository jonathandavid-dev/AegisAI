import structlog
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message
from app.conversation.summarizer import ConversationSummarizer

logger = structlog.get_logger("aegis.conversation")

class MemoryService:
    """Manages conversational history limits, slicing logs, and persisting summaries."""
    
    @staticmethod
    async def manage_memory(
        db: AsyncSession, 
        conversation: Conversation, 
        history: List[Message], 
        max_history: int = 8
    ) -> Tuple[str | None, List[Message]]:
        """Identifies older turns, prompts summaries, and returns the active messages window."""
        if len(history) <= max_history:
            return conversation.summary, history
            
        logger.info("Enforcing memory budget limits", history_count=len(history), max_history=max_history)
        
        # Split history: older messages to summarize, and recent messages to keep
        older_messages = history[:-max_history]
        recent_messages = history[-max_history:]
        
        # Summarize older logs and append to existing summary
        new_summary = ConversationSummarizer.generate_summary(older_messages, conversation.summary)
        
        # Save summary back to Conversation record
        conversation.summary = new_summary
        db.add(conversation)
        await db.commit()
        
        logger.info("Summary Generated", new_summary=new_summary)
        return new_summary, recent_messages
