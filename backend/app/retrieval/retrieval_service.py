from typing import List, Dict, Any
from app.vectorstore.chroma_client import get_collection

class RetrievalService:
    """Service interfacing with ChromaDB to fetch matching vector candidates."""
    
    @staticmethod
    def retrieve_candidates(
        query_embedding: List[float], 
        top_k: int = 10, 
        where_filter: Dict[str, Any] | None = None,
        collection_name: str = "documents"
    ) -> Dict[str, Any]:
        """Queries the ChromaDB collection with query vector and filters."""
        collection = get_collection(collection_name)
        
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }
        if where_filter:
            query_kwargs["where"] = where_filter
            
        results = collection.query(**query_kwargs)
        return results
