from typing import Dict, Any

class FilterService:
    """Helper service converting API dictionary filters into ChromaDB collection filter structures."""
    
    @staticmethod
    def compile_filters(filters: Dict[str, Any]) -> Dict[str, Any] | None:
        """Translates basic filters into a valid ChromaDB query syntax dictionary."""
        if not filters:
            return None
            
        chroma_constraints = []
        
        # 1. Map equality properties
        for key in ["document_id", "filename", "page_number", "chunk_index", "checksum"]:
            if key in filters and filters[key] is not None:
                chroma_constraints.append({key: {"$eq": filters[key]}})
                
        # 2. Map date ranges
        if "created_after" in filters and filters["created_after"]:
            chroma_constraints.append({"created_at": {"$gte": filters["created_after"]}})
        if "created_before" in filters and filters["created_before"]:
            chroma_constraints.append({"created_at": {"$lte": filters["created_before"]}})
            
        if not chroma_constraints:
            return None
            
        if len(chroma_constraints) == 1:
            return chroma_constraints[0]
            
        return {"$and": chroma_constraints}
