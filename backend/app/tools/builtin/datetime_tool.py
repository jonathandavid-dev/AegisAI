from datetime import datetime, timezone
from typing import Dict, Any
from app.tools.base_tool import BaseTool

class DateTimeTool(BaseTool):
    """Retrieves server UTC date and time."""
    
    @property
    def name(self) -> str:
        return "datetime"
        
    @property
    def description(self) -> str:
        return "Returns current date and time of the server system in UTC timezone."
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return {}
        
    def validate(self, params: Dict[str, Any]) -> bool:
        return True
        
    def execute(self, params: Dict[str, Any]) -> Any:
        now = datetime.now(timezone.utc)
        return {
            "iso": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }
