import abc
from typing import Dict, Any, List

class BaseTool(abc.ABC):
    """Abstract base class defining the schema and execution interface for system tools."""
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """System identifier for the tool."""
        pass
        
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Description of the tool capability."""
        pass
        
    @property
    @abc.abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Expected parameters schema defining names, types, and requirements."""
        pass
        
    @property
    def permissions(self) -> List[str]:
        """Access permissions required to invoke this tool."""
        return ["read"]
        
    @property
    def category(self) -> str:
        """Functional grouping tag for this tool."""
        return "utility"
        
    @property
    def version(self) -> str:
        """Semantic version tracking of this tool schema."""
        return "1.0.0"
        
    @abc.abstractmethod
    def validate(self, params: Dict[str, Any]) -> bool:
        """Performs validation assertions against incoming parameters."""
        pass
        
    @abc.abstractmethod
    def execute(self, params: Dict[str, Any]) -> Any:
        """Synchronously executes the tool operations and returns raw results."""
        pass
        
    def serialize_result(self, result: Any) -> str:
        """Converts output object details into context string representations."""
        import json
        if isinstance(result, (dict, list)):
            return json.dumps(result)
        return str(result)
        
    def health_check(self) -> bool:
        """Verifies underlying subsystems or dependencies are online."""
        return True
