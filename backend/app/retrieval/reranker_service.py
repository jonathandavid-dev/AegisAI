"""
RerankerService — Cross-encoder reranking for precision improvement.

Architecture:
  - Takes top-20 candidates from hybrid retrieval (RRF-fused vector + BM25)
  - Scores each (query, chunk) pair with a cross-encoder model
  - Returns top-5 chunks by reranker score

Model:
  BAAI/bge-reranker-base — 278M cross-encoder optimized for retrieval reranking.
  Unlike bi-encoder (embedding) models, cross-encoders process both query and
  passage together, enabling much more accurate relevance scoring (+25% precision
  improvement over bi-encoder cosine similarity alone).

Memory note:
  bge-reranker-base requires ~550MB RAM. For constrained environments, the service
  gracefully falls back to score-ordering if the model fails to load.
"""
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger("aegis.reranker")

_RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"


class RerankerService:
    """Cross-encoder reranking service for enterprise RAG precision."""
    
    _model = None
    _model_loaded = False
    _load_failed = False

    @classmethod
    def _get_model(cls):
        """Lazy-load the cross-encoder model."""
        if cls._load_failed:
            return None
        if cls._model is not None:
            return cls._model
        
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading reranker model...", model=_RERANKER_MODEL_NAME)
            cls._model = CrossEncoder(_RERANKER_MODEL_NAME, max_length=512)
            cls._model_loaded = True
            logger.info("Reranker model loaded", model=_RERANKER_MODEL_NAME)
        except Exception as exc:
            logger.warning(
                "Reranker model load failed — falling back to score ordering",
                error=str(exc)
            )
            cls._load_failed = True
            cls._model = None
        
        return cls._model

    @classmethod
    def rerank(
        cls,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder scores.
        
        Parameters
        ----------
        query : str
            The original (non-expanded) user query.
        candidates : List[Dict]
            Up to 20 chunks from hybrid retrieval with RRF scores.
        top_k : int
            Number of top chunks to return (default: 5).
        
        Returns
        -------
        List[Dict] — top_k chunks sorted by reranker score descending,
        with 'reranker_score' field added.
        """
        if not candidates:
            return []
        
        model = cls._get_model()
        
        if model is None:
            # Fallback: return top_k sorted by rrf_score or score
            logger.info("Reranker fallback: using RRF/vector scores")
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get("rrf_score", x.get("score", 0)),
                reverse=True
            )
            for c in sorted_candidates:
                c["reranker_score"] = c.get("rrf_score", c.get("score", 0.0))
            return sorted_candidates[:top_k]
        
        try:
            # Build (query, passage) pairs for cross-encoder
            pairs = [(query, c.get("content", "")) for c in candidates]
            
            # Score all pairs — cross-encoder returns raw logit scores
            scores = model.predict(pairs, show_progress_bar=False)
            
            # Attach reranker scores
            for i, candidate in enumerate(candidates):
                raw_score = float(scores[i])
                # Normalize to [0, 1] via sigmoid
                import math
                normalized = 1.0 / (1.0 + math.exp(-raw_score))
                candidate["reranker_score"] = normalized
            
            # Sort by reranker score descending
            reranked = sorted(candidates, key=lambda x: x["reranker_score"], reverse=True)
            
            logger.info(
                "Reranking complete",
                candidates=len(candidates),
                returned=min(top_k, len(reranked)),
                top_score=reranked[0]["reranker_score"] if reranked else 0
            )
            
            return reranked[:top_k]
            
        except Exception as exc:
            logger.error("Reranker inference failed", error=str(exc))
            # Fallback to score ordering
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get("rrf_score", x.get("score", 0)),
                reverse=True
            )
            for c in sorted_candidates:
                c["reranker_score"] = c.get("score", 0.0)
            return sorted_candidates[:top_k]
