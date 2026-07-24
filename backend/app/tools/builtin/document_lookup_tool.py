from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.search.search_service import SearchService

class DocumentLookupTool(BaseTool):
    """Filters vector queries specifically within a single document filename matching context."""
    
    @property
    def name(self) -> str:
        return "document_lookup"
        
    @property
    def description(self) -> str:
        return "Searches context segments specifically restricted to a single filename in the knowledge base."
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Topic or context to locate inside the file",
                "required": True
            },
            "filename": {
                "type": "string",
                "description": "Exact storage or original filename of the document to inspect",
                "required": True
            }
        }
        
    def validate(self, params: Dict[str, Any]) -> bool:
        if "query" not in params or not isinstance(params["query"], str):
            return False
        if "filename" not in params or not isinstance(params["filename"], str):
            return False
        return len(params["query"].strip()) > 0 and len(params["filename"].strip()) > 0
        
    def execute(self, params: Dict[str, Any]) -> Any:
        query = params["query"]
        filename = params["filename"]
        filters = {"filename": filename}
        workspace_id = params.get("workspace_id", 1)
        from app.utils.async_utils import run_sync
        return run_sync(SearchService.search(query=query, workspace_id=workspace_id, top_k=5, similarity_threshold=0.50, filters=filters))

