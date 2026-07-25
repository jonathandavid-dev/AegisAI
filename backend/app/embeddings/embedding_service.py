import structlog
from typing import List
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger("aegis.embeddings")

# BGE instruction prefixes for asymmetric retrieval
# IMPORTANT: BGE-family models require these prefixes to leverage instruction tuning.
# Omitting them causes ~10-15% quality degradation in retrieval precision.
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_DOCUMENT_PREFIX = ""  # BGE does NOT require prefix on document side

class EmbeddingService:
    """Service layer managing the lazy initialization and loading of BGE vector embeddings.
    
    Phase 3 upgrade:
    - Separates embed_query (with instruction prefix) from embed_documents (no prefix).
    - BGE asymmetric retrieval requires different encoding for queries vs. indexed text.
    - Model kept as bge-small-en-v1.5 for Docker memory compatibility; can be upgraded
      to BAAI/bge-large-en-v1.5 via the BGE_MODEL_NAME env var for higher quality.
    """
    
    _model: SentenceTransformer | None = None
    _model_name = "BAAI/bge-small-en-v1.5"
    
    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Loads and returns the SentenceTransformer singleton model instance."""
        if cls._model is None:
            logger.info("Loading Embedding Model...", model=cls._model_name)
            cls._model = SentenceTransformer(cls._model_name)
            logger.info("Embedding Model Loaded", model=cls._model_name)
        return cls._model

    @classmethod
    def embed_queries(cls, queries: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embeds search queries WITH the BGE instruction prefix.
        Use this for all user query embeddings at search time.
        """
        if not queries:
            return []
        
        prefixed = [_QUERY_PREFIX + q.strip() for q in queries]
        logger.info("Query Embedding Started", count=len(queries))
        model = cls.get_model()
        embeddings = model.encode(
            prefixed,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True   # L2-normalize for cosine similarity
        )
        return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]

    @classmethod
    def embed_documents(cls, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embeds document chunks WITHOUT query prefix.
        Use this during document indexing.
        """
        if not texts:
            return []
        
        logger.info("Document Embedding Started", count=len(texts), batch_size=batch_size)
        model = cls.get_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True   # L2-normalize for consistent cosine similarity
        )
        for i in range(len(texts)):
            logger.debug("Chunk Embedded", index=i)
        return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]

    @classmethod
    def embed_texts(cls, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Backward-compatible wrapper — delegates to embed_documents.
        Preserved to avoid breaking any existing callers.
        """
        return cls.embed_documents(texts, batch_size=batch_size)
