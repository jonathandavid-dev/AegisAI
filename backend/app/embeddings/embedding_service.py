import structlog
from typing import List
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger("aegis.embeddings")

class EmbeddingService:
    """Service layer managing the lazy initialization and loading of BGE vector embeddings."""
    
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
    def embed_texts(cls, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Calculates BGE small vector embeddings for a list of string segments.
        Iterates in configurations matching the defined batch size.
        """
        if not texts:
            return []
            
        logger.info("Embedding Generation Started", count=len(texts), batch_size=batch_size)
        model = cls.get_model()
        
        # SentenceTransformers encode handles batch boundaries natively
        embeddings = model.encode(
            texts, 
            batch_size=batch_size, 
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Log embedding completions
        for i in range(len(texts)):
            logger.debug("Chunk Embedded", index=i)
            
        return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]
