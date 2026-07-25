import structlog
from typing import List, Dict, Any

logger = structlog.get_logger("aegis.citation")

class CitationBuilder:
    """Builds rich reference list objects mapping context sources to documents.
    
    Phase 9 upgrade:
    - Includes section and heading metadata in citations.
    - Includes similarity score and reranker score for diagnostics.
    - Includes a short chunk content preview for the frontend citation modal.
    - Citations are numbered consistently with [Source N] markers in the answer.
    """
    
    @staticmethod
    def build_citations(selected_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Builds deduplicated rich citation objects from selected context chunks.
        
        Output per citation:
          - document_id, filename, page_number, chunk_index
          - section, heading (enterprise metadata)
          - similarity_score, reranker_score (diagnostics)
          - content_preview (first 200 chars for frontend display)
          - source_number (matches [Source N] in answer text)
        """
        citations = []
        seen = set()
        
        for idx, item in enumerate(selected_chunks):
            doc_id = item.get("document_id", 0)
            page = item.get("page_number", 1)
            chunk_idx = item.get("chunk_index", 0)
            filename = item.get("filename", "Unknown")
            section = item.get("section", "")
            heading = item.get("heading", "")
            content = item.get("content", "")
            score = item.get("score", 0.0)
            reranker_score = item.get("reranker_score", score)
            chunk_type = item.get("chunk_type", "paragraph")
            
            key = (doc_id, filename, page, chunk_idx)
            if key not in seen:
                seen.add(key)
                citations.append({
                    "source_number": idx + 1,       # Matches [Source N] in answer
                    "document_id": doc_id,
                    "filename": filename,
                    "page_number": page,
                    "chunk_index": chunk_idx,
                    "section": section,
                    "heading": heading,
                    "chunk_type": chunk_type,
                    "similarity_score": round(score, 4),
                    "reranker_score": round(reranker_score, 4),
                    "content_preview": content[:250].strip() + ("..." if len(content) > 250 else ""),
                })
                
        logger.info("Citation Generation Completed", count=len(citations))
        return citations
