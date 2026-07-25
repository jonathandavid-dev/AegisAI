import structlog
from typing import List, Dict, Any, Tuple
from app.config.settings import settings

logger = structlog.get_logger("aegis.context")

class ContextBuilder:
    """Formats retrieved document segments into a rich context string for system prompts.
    
    Phase 9 upgrade:
    - Each source block includes section/heading metadata for the LLM to reference.
    - Chunks are deduplicated by chunk_id before formatting.
    - Token budget is enforced using the ~4 chars/token heuristic.
    - Source numbering is consistent with [Source N] inline citation markers.
    """
    
    @staticmethod
    def build_context(
        results: List[Dict[str, Any]], 
        max_chunks: int = None, 
        max_tokens: int = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Filters duplicates and assembles a rich context string under token limits.
        
        Each source block format:
            [Source N: filename | Page X | Section: Y | Heading: Z]
            chunk content...
        """
        if max_chunks is None:
            max_chunks = settings.MAX_CONTEXT_CHUNKS
        if max_tokens is None:
            max_tokens = settings.MAX_CONTEXT_TOKENS
            
        logger.info(
            "context_build_started",
            input_chunks=len(results),
            max_chunks=max_chunks,
            max_tokens=max_tokens
        )
        
        # 1. Deduplicate by chunk_id (exact match)
        seen_ids = set()
        unique_results = []
        for item in results:
            cid = item.get("chunk_id")
            if cid not in seen_ids:
                seen_ids.add(cid)
                unique_results.append(item)
                
        # 2. Slice to chunk limit
        unique_results = unique_results[:max_chunks]
        
        # 3. Token-budget enforcement (heuristic: 1 token ≈ 4 chars)
        selected_chunks = []
        current_tokens = 0
        
        for item in unique_results:
            content = item.get("content", "")
            tokens_needed = len(content) // 4
            if current_tokens + tokens_needed > max_tokens:
                logger.warning("context_token_budget_exceeded", chunk_id=item.get("chunk_id"))
                break
            selected_chunks.append(item)
            current_tokens += tokens_needed
            
        # 4. Format rich context blocks
        blocks = []
        for idx, item in enumerate(selected_chunks):
            source_num = idx + 1
            filename = item.get("filename", "Unknown")
            page = item.get("page_number", 1)
            chunk_idx = item.get("chunk_index", 0)
            content = item.get("content", "").strip()
            section = item.get("section", "")
            heading = item.get("heading", "")
            chunk_type = item.get("chunk_type", "paragraph")
            reranker_score = item.get("reranker_score", item.get("score", 0.0))
            
            # Build rich header
            header_parts = [f"[Source {source_num}: {filename}"]
            header_parts.append(f"Page {page}")
            if section:
                header_parts.append(f"Section: {section}")
            if heading and heading != section:
                header_parts.append(f"Heading: {heading}")
            if chunk_type != "paragraph":
                header_parts.append(f"Type: {chunk_type}")
            header_parts.append(f"Relevance: {reranker_score:.2f}]")
            
            header = " | ".join(header_parts[:1]) + " | " + " | ".join(header_parts[1:])
            
            block = f"{header}\n{content}"
            blocks.append(block)
            
        context_str = "\n\n---\n\n".join(blocks)
        logger.info(
            "Context Built",
            selected_chunks=len(selected_chunks),
            estimated_tokens=current_tokens
        )
        return context_str, selected_chunks
