"""
FusionService — Reciprocal Rank Fusion (RRF) for hybrid retrieval.

RRF Formula:
  RRF_score(d) = Σ  1 / (k + rank_i(d))
where k=60 is the RRF constant and rank_i(d) is document d's rank in result list i.

After fusion, near-duplicate chunks are detected using cosine similarity of their
text embeddings. If two chunks have cosine similarity > 0.92, the lower-ranked one
is dropped to maximize context diversity.
"""
import structlog
from typing import List, Dict, Any, Set

logger = structlog.get_logger("aegis.fusion")

# RRF constant — 60 is the standard from the original paper
_RRF_K = 60


class FusionService:
    """Combines vector search and BM25 results using Reciprocal Rank Fusion."""

    @staticmethod
    def reciprocal_rank_fusion(
        result_lists: List[List[Dict[str, Any]]],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple ranked result lists via RRF.
        
        Each result dict must contain a 'chunk_id' key.
        The output list is sorted by RRF score descending, deduplicated by chunk_id.
        """
        rrf_scores: Dict[str, float] = {}
        chunk_registry: Dict[str, Dict[str, Any]] = {}   # chunk_id -> best result dict
        
        for result_list in result_lists:
            for rank, result in enumerate(result_list):
                chunk_id = result.get("chunk_id", f"unknown_{rank}")
                rrf_score = 1.0 / (_RRF_K + rank + 1)
                
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score
                
                # Keep the version with the highest original score
                if chunk_id not in chunk_registry:
                    chunk_registry[chunk_id] = result
                else:
                    existing = chunk_registry[chunk_id]
                    if result.get("score", 0) > existing.get("score", 0):
                        chunk_registry[chunk_id] = result
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        
        merged: List[Dict[str, Any]] = []
        for chunk_id in sorted_ids[:top_k]:
            result = dict(chunk_registry[chunk_id])
            result["rrf_score"] = rrf_scores[chunk_id]
            merged.append(result)
        
        logger.info(
            "RRF fusion complete",
            input_lists=len(result_lists),
            merged_count=len(merged)
        )
        return merged

    @staticmethod
    def deduplicate_near_dupes(
        results: List[Dict[str, Any]],
        similarity_threshold: float = 0.92
    ) -> List[Dict[str, Any]]:
        """
        Remove near-duplicate chunks from a ranked result list.
        
        Two chunks are considered near-duplicates if their text overlap (Jaccard
        similarity on word sets) exceeds the threshold. The lower-ranked chunk
        (later in the list) is dropped.
        
        Uses word-set Jaccard similarity — fast, no extra model calls needed.
        """
        if len(results) <= 1:
            return results
        
        def word_set(text: str) -> Set[str]:
            import re
            return set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower()))
        
        kept: List[Dict[str, Any]] = []
        kept_word_sets: List[Set[str]] = []
        
        for result in results:
            content = result.get("content", "")
            ws = word_set(content)
            
            is_dupe = False
            for existing_ws in kept_word_sets:
                if not ws or not existing_ws:
                    continue
                intersection = ws & existing_ws
                union = ws | existing_ws
                jaccard = len(intersection) / len(union) if union else 0.0
                if jaccard >= similarity_threshold:
                    is_dupe = True
                    break
            
            if not is_dupe:
                kept.append(result)
                kept_word_sets.append(ws)
        
        removed = len(results) - len(kept)
        if removed > 0:
            logger.info("Near-duplicate chunks removed", removed=removed, kept=len(kept))
        
        return kept
