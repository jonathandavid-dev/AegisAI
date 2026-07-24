import re
import structlog
from typing import Dict, Any

logger = structlog.get_logger("aegis.agents")

class Planner:
    """Parses parameters and generates single-turn execution plans for selected tools."""
    
    @staticmethod
    def generate_plan(question: str, intent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Maps user question text to tool-specific execution schemas."""
        tool_name = intent_info.get("tool_required")
        logger.info("Planning", tool_required=tool_name)
        
        if not tool_name:
            return {"tool_name": None, "parameters": {}}
            
        params = {}
        
        if tool_name == "calculator":
            # Strip "calculate" prefixes to isolate arithmetic text
            match = re.search(r"(?:calculate|evaluate)\s+(.*)", question, re.IGNORECASE)
            expr = match.group(1) if match else question
            
            # Map common words to basic arithmetic characters
            expr = expr.replace("of", "*")
            expr = expr.replace("%", " * 0.01")
            expr = expr.replace("divided by", "/")
            expr = expr.replace("times", "*")
            params = {"expression": expr.strip()}
            
        elif tool_name == "datetime":
            params = {}
            
        elif tool_name == "document_lookup":
            # Extract filename (e.g. "handbook.pdf")
            file_match = re.search(r"(\w+\.(?:pdf|docx|txt))", question, re.IGNORECASE)
            filename = file_match.group(1) if file_match else "security_policy.pdf"
            
            # Extract query by clearing lookup operators
            clean_q = question
            for keyword in ["look up", "find in", "restricted to", "search inside", "lookup in", filename]:
                clean_q = re.sub(keyword, "", clean_q, flags=re.IGNORECASE)
                
            params = {
                "query": clean_q.strip(),
                "filename": filename
            }
            
        elif tool_name == "enterprise_search":
            params = {"query": question}
            
        return {
            "tool_name": tool_name,
            "parameters": params
        }
