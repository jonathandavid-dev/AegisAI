from typing import List
from app.models.conversation import Message

class HistoryService:
    """Standardizes dialogue exchanges into clean text prompts."""
    
    @staticmethod
    def format_history_for_prompt(messages: List[Message]) -> str:
        """Joins messages by uppercase role labels."""
        lines = []
        for msg in messages:
            role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            lines.append(f"{role_str.upper()}: {msg.content}")
        return "\n".join(lines)
