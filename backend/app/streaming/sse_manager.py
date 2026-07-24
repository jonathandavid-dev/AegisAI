import json
from typing import Any, Optional

class SSEManager:
    """Helper class for formatting structured messages into standard Server-Sent Events (SSE) lines."""
    
    @staticmethod
    def format_event(data: Any, event_type: Optional[str] = None) -> str:
        """Serializes dictionary payloads into data-only or typed event SSE payloads."""
        payload = json.dumps(data)
        if event_type:
            return f"event: {event_type}\ndata: {payload}\n\n"
        return f"data: {payload}\n\n"
