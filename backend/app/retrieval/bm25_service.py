"""
BM25Service — Workspace-scoped BM25 keyword index for hybrid retrieval.

Architecture:
  - One BM25Okapi index per workspace, built lazily on first search.
  - Index is stored in-process memory (fast, no extra infrastructure).
  - Invalidated on document upload/delete via BM25Service.invalidate(workspace_id).
  - Corpus is loaded from ChromaDB so it stays in sync with the vector store.

Why BM25:
  Vector search excels at semantic similarity but fails on exact keyword matches
  (acronyms, product names, version numbers, proper nouns). BM25 fills this gap.
"""
import structlog
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

logger = structlog.get_logger("aegis.bm25")

# In-memory per-workspace index registry
# Structure: {workspace_id: {"index": BM25Okapi, "corpus": [str], "metadatas": [...], "ids": [str]}}
_indices: Dict[int, Dict[str, Any]] = {}


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    import re
    tokens = re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())
    return tokens


class BM25Service:
    """BM25 keyword retrieval service scoped to workspace collections."""

    @classmethod
    def invalidate(cls, workspace_id: int) -> None:
        """Drop the cached BM25 index for a workspace (called on document add/delete)."""
        if workspace_id in _indices:
            del _indices[workspace_id]
            logger.info("BM25 index invalidated", workspace_id=workspace_id)

    @classmethod
    def _build_index(cls, workspace_id: int) -> None:
        """Build and cache the BM25 index from the workspace ChromaDB collection."""
        from app.vectorstore.chroma_client import get_collection
        
        try:
            collection = get_collection(f"workspace_{workspace_id}")
            # Fetch all documents from ChromaDB
            all_docs = collection.get(include=["documents", "metadatas"])
            
            ids: List[str] = all_docs.get("ids", [])
            documents: List[str] = all_docs.get("documents", []) or []
            metadatas: List[Dict] = all_docs.get("metadatas", []) or []
            
            if not documents:
                logger.info("BM25 build skipped — no documents in workspace", workspace_id=workspace_id)
                _indices[workspace_id] = {
                    "index": None,
                    "corpus": [],
                    "metadatas": [],
                    "ids": []
                }
                return
            
            tokenized_corpus = [_tokenize(doc) for doc in documents]
            bm25_index = BM25Okapi(tokenized_corpus)
            
            _indices[workspace_id] = {
                "index": bm25_index,
                "corpus": documents,
                "metadatas": metadatas,
                "ids": ids
            }
            logger.info("BM25 index built", workspace_id=workspace_id, doc_count=len(documents))
            
        except Exception as exc:
            logger.error("BM25 index build failed", workspace_id=workspace_id, error=str(exc))
            _indices[workspace_id] = {"index": None, "corpus": [], "metadatas": [], "ids": []}

    @classmethod
    def search(
        cls,
        query: str,
        workspace_id: int,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword retrieval for the given query.
        
        Returns a list of result dicts matching the format of ChromaDB ranked results:
        {document_id, chunk_id, filename, page_number, chunk_index, score, content,
         section, heading, keywords, chunk_type}
        """
        # Build index lazily
        if workspace_id not in _indices:
            cls._build_index(workspace_id)
        
        idx_data = _indices[workspace_id]
        bm25_index: Optional[BM25Okapi] = idx_data.get("index")
        corpus = idx_data.get("corpus", [])
        metadatas = idx_data.get("metadatas", [])
        ids = idx_data.get("ids", [])
        
        if bm25_index is None or not corpus:
            return []
        
        tokens = _tokenize(query)
        if not tokens:
            return []
        
        scores = bm25_index.get_scores(tokens)
        
        # Gather top_k results above score 0
        indexed_scores = [(i, float(s)) for i, s in enumerate(scores) if s > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_results = indexed_scores[:top_k]
        
        results = []
        max_score = max((s for _, s in top_results), default=1.0) or 1.0
        
        for idx, raw_score in top_results:
            if idx >= len(corpus):
                continue
            meta = metadatas[idx] if idx < len(metadatas) else {}
            normalized_score = raw_score / max_score   # Normalize to [0, 1]
            
            results.append({
                "document_id": int(meta.get("document_id", 0)),
                "chunk_id": ids[idx] if idx < len(ids) else f"bm25_{idx}",
                "filename": meta.get("filename", "Unknown"),
                "page_number": int(meta.get("page_number", 1)),
                "chunk_index": int(meta.get("chunk_index", idx)),
                "score": normalized_score,
                "bm25_score": normalized_score,
                "content": corpus[idx],
                "section": meta.get("section", ""),
                "heading": meta.get("heading", ""),
                "keywords": meta.get("keywords", ""),
                "chunk_type": meta.get("chunk_type", "paragraph"),
                "hierarchy_level": int(meta.get("hierarchy_level", 2)),
                "retrieval_source": "bm25"
            })
        
        return results
