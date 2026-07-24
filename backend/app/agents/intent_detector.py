import structlog
from typing import Dict, Any

logger = structlog.get_logger("aegis.agents")

class IntentDetector:
    """Classifies user queries to identify required tool or retrieval loops."""
    
    @staticmethod
    def detect_intent(question: str) -> Dict[str, Any]:
        """Examines user query strings and maps them to a category intent."""
        logger.info("Intent Detection", question=question)
        
        q_lower = question.lower()
        
        # 1. Math/Calculator expressions check
        math_words = ["calculate", "evaluate", "math", "sum of", "product of", "divided by"]
        math_chars = ["+", "-", "*", "/"]
        is_math = any(w in q_lower for w in math_words) or any(c in q_lower for c in math_chars if c != "-")
        if is_math and any(char.isdigit() for char in q_lower):
            return {
                "intent": "TOOL",
                "tool_required": "calculator",
                "confidence": 0.95
            }
            
        # 2. DateTime clock queries check
        time_words = ["time", "date", "clock", "what day", "current year"]
        if any(w in q_lower for w in time_words):
            return {
                "intent": "TOOL",
                "tool_required": "datetime",
                "confidence": 0.95
            }
            
        # 3. Restricted Document lookups check
        lookup_words = ["look up", "find in", "restricted to", "search inside", "lookup in"]
        if any(w in q_lower for w in lookup_words):
            return {
                "intent": "HYBRID",
                "tool_required": "document_lookup",
                "confidence": 0.85
            }
            
        # 4. Standard RAG semantic search check
        rag_words = ["policy", "guideline", "security", "handbook", "requirement", "manual"]
        if any(w in q_lower for w in rag_words):
            return {
                "intent": "RETRIEVAL",
                "tool_required": "enterprise_search",
                "confidence": 0.90
            }
            
        # 5. Dialogue/Casual conversation fallback
        return {
            "intent": "CONVERSATION",
            "tool_required": None,
            "confidence": 1.0
        }
