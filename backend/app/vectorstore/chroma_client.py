import os
import chromadb
from app.core.logging import app_logger

CHROMA_PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "storage", 
    "chromadb"
)

# Ensure directory is ready
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    app_logger.info("chromadb_client_initialized", persist_path=CHROMA_PERSIST_DIR)
except Exception as exc:
    app_logger.error("chromadb_client_failed", error=str(exc))
    raise exc

def get_collection(name: str = "documents"):
    """
    Retrieves or instantiates a persistent Chroma collection.
    No default embedding functions are configured to preserve 
    encapsulation in the EmbeddingService.
    """
    return chroma_client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )
