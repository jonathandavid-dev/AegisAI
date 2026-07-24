import structlog
from typing import List, Dict, Any, Tuple
from app.config.settings import settings

logger = structlog.get_logger("aegis.context")

class ContextBuilder:
    """Formats and budget-caps retrieved document segments for system prompts."""
    
    @staticmethod
    def build_context(
        results: List[Dict[str, Any]], 
        max_chunks: int = None, 
        max_tokens: int = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Filters duplicates and slices vector segments under limits to assemble a context string."""
        if max_chunks is None:
            max_chunks = settings.MAX_CONTEXT_CHUNKS
        if max_tokens is None:
            max_tokens = settings.MAX_CONTEXT_TOKENS
            
        logger.info("context_build_started", input_chunks=len(results), max_chunks=max_chunks, max_tokens=max_tokens)
        
        # 1. Deduplicate by chunk_id
        seen_ids = set()
        unique_results = []
        for item in results:
            cid = item.get("chunk_id")
            if cid not in seen_ids:
                seen_ids.add(cid)
                unique_results.append(item)
                
        # 2. Slice to limit
        unique_results = unique_results[:max_chunks]
        
        # 3. Fit in token budget (heuristic: 1 token = ~4 chars)
        selected_chunks = []
        current_tokens = 0
        
        for item in unique_results:
            content = item.get("content", "")
            tokens_needed = len(content) // 4
            if current_tokens + tokens_needed > max_tokens:
                logger.warn("context_token_budget_exceeded", chunk_id=item.get("chunk_id"))
                break
            selected_chunks.append(item)
            current_tokens += tokens_needed
            
        # 4. Format string block
        blocks = []
        for idx, item in enumerate(selected_chunks):
            filename = item.get("filename", "Unknown")
            page = item.get("page_number", 1)
            chunk_idx = item.get("chunk_index", 0)
            content = item.get("content", "").strip()
            
            block = f"[Source {idx+1}: {filename} (Page {page}, Chunk {chunk_idx})]\n{content}"
            blocks.append(block)
            
        context_str = "\n\n".join(blocks)
        logger.info("Context Built", selected_chunks=len(selected_chunks), estimated_tokens=current_tokens)
        return context_str, selected_chunks
