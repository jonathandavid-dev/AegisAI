from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.search.search_service import SearchService

class SearchTool(BaseTool):
    """Integrates semantic vector search into the tool orchestrator framework."""
    
    @property
    def name(self) -> str:
        return "enterprise_search"
        
    @property
    def description(self) -> str:
        return "Queries document segments from the vector knowledge base using semantic search."
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Semantic search query, e.g. 'health benefit eligibility'",
                "required": True
            },
            "top_k": {
                "type": "integer",
                "description": "Max segments count (default: 5)",
                "required": False
            }
        }
        
    def validate(self, params: Dict[str, Any]) -> bool:
        if "query" not in params or not isinstance(params["query"], str):
            return False
        return len(params["query"].strip()) > 0
        
    def execute(self, params: Dict[str, Any]) -> Any:
        query = params["query"]
        top_k = params.get("top_k", 5)
        workspace_id = params.get("workspace_id", 1)
        from app.utils.async_utils import run_sync
        return run_sync(SearchService.search(query=query, workspace_id=workspace_id, top_k=top_k, similarity_threshold=0.50))


