import structlog
from typing import List, Dict, Any
from app.vectorstore.chroma_client import get_collection

logger = structlog.get_logger("aegis.vectorstore")

class VectorService:
    """Service layer managing writes and deletes within the vector database."""
    
    @staticmethod
    def upsert_chunks(
        ids: List[str], 
        embeddings: List[List[float]], 
        documents: List[str], 
        metadatas: List[Dict[str, Any]],
        collection_name: str = "documents"
    ) -> None:
        """Upserts a batch of chunk vectors and metadata properties into ChromaDB."""
        if not ids:
            return
            
        collection = get_collection(collection_name)
        
        # Chroma collection insertion
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        # Log successful vector persistences
        for chunk_id in ids:
            logger.info("Vector Stored", chunk_id=chunk_id)
            
    @staticmethod
    def delete_document_vectors(document_id: int, collection_name: str = "documents") -> None:
        """Removes all stored vectors associated with a document from ChromaDB."""
        collection = get_collection(collection_name)
        collection.delete(where={"document_id": document_id})
        logger.info("document_vectors_deleted", document_id=document_id)
