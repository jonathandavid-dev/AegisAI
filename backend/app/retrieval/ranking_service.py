from typing import List, Dict, Any

class RankingService:
    """Service responsible for sorting, threshold-filtering, and formatting search results."""
    
    @staticmethod
    def rank_results(
        chroma_results: Dict[str, Any], 
        similarity_threshold: float = 0.50, 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Transforms distance metrics into similarity scores and drops records below threshold."""
        ranked_items = []
        
        # Extract Chroma nested lists
        ids = chroma_results.get("ids", [[]])[0]
        distances = chroma_results.get("distances", [[]])[0]
        documents = chroma_results.get("documents", [[]])[0]
        metadatas = chroma_results.get("metadatas", [[]])[0]
        
        for idx in range(len(ids)):
            # Convert cosine distance to similarity score
            distance = distances[idx]
            score = 1.0 - distance
            
            # Clamp value boundaries
            score = max(0.0, min(1.0, score))
            
            # Exclude low-relevance results
            if score < similarity_threshold:
                continue
                
            metadata = metadatas[idx] or {}
            
            item = {
                "document_id": int(metadata.get("document_id", 0)),
                "chunk_id": ids[idx],
                "filename": metadata.get("filename", "Unknown"),
                "page_number": int(metadata.get("page_number", 1)),
                "chunk_index": int(metadata.get("chunk_index", 0)),
                "score": score,
                "content": documents[idx] or ""
            }
            
            ranked_items.append(item)
            
        # Sort by similarity score descending
        ranked_items.sort(key=lambda x: x["score"], reverse=True)
        
        return ranked_items[:top_k]
