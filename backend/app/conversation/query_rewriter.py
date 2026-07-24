import structlog
from typing import List
from app.models.conversation import Message
from app.llm.llm_client import LLMClient

logger = structlog.get_logger("aegis.conversation")

class QueryRewriter:
    """Uses LLM text generation to resolve ambiguity in conversational follow-up questions."""
    
    @staticmethod
    def rewrite_query(history: List[Message], current_question: str) -> str:
        """Translates follow-up user query into a context-independent search question."""
        if not history:
            return current_question
            
        logger.info("Query Rewriter Started", current_question=current_question)
        
        # Format recent history turns (limit to last 5 for context window)
        history_lines = []
        for msg in history[-5:]:
            history_lines.append(f"{msg.role}: {msg.content}")
        history_context = "\n".join(history_lines)
        
        # Build prompt instructing the LLM to rewrite the question
        prompt = (
            "SYSTEM\n"
            "Given the following conversation history and a follow-up question, "
            "rewrite it into a standalone question that can be understood on its own "
            "WITHOUT context history. Keep the language natural and clear. "
            "Do NOT answer the question. Just output the rewritten question.\n"
            "--------------------------------\n"
            f"CONVERSATION HISTORY\n{history_context}\n"
            "--------------------------------\n"
            f"FOLLOW-UP QUESTION\n{current_question}\n"
            "--------------------------------\n"
            "STANDALONE QUESTION:"
        )
        
        rewritten = LLMClient.generate(prompt).strip()
        
        # Clean potential output prefixes
        if rewritten.startswith("STANDALONE QUESTION:"):
            rewritten = rewritten.replace("STANDALONE QUESTION:", "").strip()
            
        # Mock provider grounding check mapping
        if "[Mock Grounded Answer]" in rewritten or "I am sorry" in rewritten:
            rewritten = f"Standalone query about: {current_question}"
            
        logger.info("Query Rewritten", original=current_question, rewritten=rewritten)
        return rewritten
