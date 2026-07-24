import structlog
from typing import Dict, List
from app.tools.base_tool import BaseTool

logger = structlog.get_logger("aegis.tools")

class ToolRegistry:
    """Central catalog orchestrating dynamic registration and lookup of BaseTool items."""
    
    _registry: Dict[str, BaseTool] = {}
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Binds a tool instance to the registry lookup indexing map."""
        name_key = tool.name.lower()
        cls._registry[name_key] = tool
        logger.info("Tool Registered", name=tool.name, category=tool.category, version=tool.version)
        
    @classmethod
    def get_tool(cls, name: str) -> BaseTool | None:
        """Retrieves a registered tool instance by its identifier."""
        return cls._registry.get(name.lower())
        
    @classmethod
    def list_tools(cls) -> List[BaseTool]:
        """Lists all active tool singletons currently registered."""
        return list(cls._registry.values())
        
    @classmethod
    def clear(cls) -> None:
        """Removes all items from the catalog (primarily for test resets)."""
        cls._registry.clear()
        
    @classmethod
    def register_builtin_tools(cls) -> None:
        """Loads and registers all default enterprise built-in singletons."""
        from app.tools.builtin.calculator_tool import CalculatorTool
        from app.tools.builtin.datetime_tool import DateTimeTool
        from app.tools.builtin.search_tool import SearchTool
        from app.tools.builtin.document_lookup_tool import DocumentLookupTool
        
        cls.register(CalculatorTool())
        cls.register(DateTimeTool())
        cls.register(SearchTool())
        cls.register(DocumentLookupTool())
