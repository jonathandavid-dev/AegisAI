import structlog
from typing import List, Dict, Any

logger = structlog.get_logger("aegis.citation")

class CitationBuilder:
    """Builds reference list objects mapping context sources to documents."""
    
    @staticmethod
    def build_citations(selected_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates and maps input segments to JSON reference schemas."""
        citations = []
        seen = set()
        
        for item in selected_chunks:
            doc_id = item.get("document_id", 0)
            page = item.get("page_number", 1)
            chunk_idx = item.get("chunk_index", 0)
            filename = item.get("filename", "Unknown")
            
            key = (doc_id, filename, page, chunk_idx)
            if key not in seen:
                seen.add(key)
                citations.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "page_number": page,
                    "chunk_index": chunk_idx
                })
                
        logger.info("Citation Generation Completed", count=len(citations))
        return citations
