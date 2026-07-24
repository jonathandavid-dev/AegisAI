import structlog
from typing import List
from app.models.conversation import Message
from app.llm.llm_client import LLMClient

logger = structlog.get_logger("aegis.conversation")

class ConversationSummarizer:
    """Invokes active LLM providers to condense chat histories and store summaries."""
    
    @staticmethod
    def generate_summary(history: List[Message], existing_summary: str | None = None) -> str:
        """Assembles dialogue logs and prompts completion to generate summaries."""
        logger.info("Summary Generated")
        
        msg_lines = []
        for msg in history:
            msg_lines.append(f"{msg.role}: {msg.content}")
        new_dialog = "\n".join(msg_lines)
        
        prompt = (
            "SYSTEM\n"
            "Summarize the main topics, questions, and decisions discussed in the conversation history. "
            "Focus on corporate policies, security topics, or guidelines mentioned. "
            "Keep the summary brief and factual. Do not exceed 150 words.\n"
            "--------------------------------\n"
            f"EXISTING SUMMARY\n{existing_summary or 'No summary yet.'}\n"
            "--------------------------------\n"
            f"NEW DIALOGUE EXCHANGES\n{new_dialog}\n"
            "--------------------------------\n"
            "SUMMARY:"
        )
        
        summary = LLMClient.generate(prompt).strip()
        if summary.startswith("SUMMARY:"):
            summary = summary.replace("SUMMARY:", "").strip()
            
        # Clean response under Mock provider
        if "[Mock Grounded Answer]" in summary or "I am sorry" in summary:
            topics = [msg.content[:30] for msg in history if msg.role == "USER"]
            summary = f"[Mock Summary] Discussion about: {', '.join(topics)}"
            
        return summary
