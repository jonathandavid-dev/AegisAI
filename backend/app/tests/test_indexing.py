import sys
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.models.document import Document
from app.models.document_chunk import DocumentChunk, ChunkEmbeddingStatus
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.vector_service import VectorService
from app.indexing.indexing_service import IndexingService
from app.workers.tasks import generate_embeddings

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_sentence_transformer():
    with patch("app.embeddings.embedding_service.SentenceTransformer") as mock_class:
        mock_model = MagicMock()
        mock_model.encode.side_effect = lambda texts, **kwargs: [[0.1] * 384 for _ in texts]
        mock_class.return_value = mock_model
        EmbeddingService._model = None
        yield mock_model
        EmbeddingService._model = None

@pytest.fixture(autouse=True)
def mock_chroma_client():
    with patch("app.vectorstore.chroma_client.chroma_client") as mock_client:
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        yield mock_collection

@pytest.fixture
def mock_account():
    account = Account()
    account.id = 1
    account.email = "test@example.com"
    account.hashed_password = "hashed_password"
    account.is_active = True
    account.created_at = datetime.now(timezone.utc)
    return account

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    
    async def mock_refresh(instance):
        if hasattr(instance, "id") and not instance.id:
            instance.id = 1
        if hasattr(instance, "created_at") and not instance.created_at:
            instance.created_at = datetime.now(timezone.utc)
        if hasattr(instance, "updated_at") and not instance.updated_at:
            instance.updated_at = datetime.now(timezone.utc)
            
    db.refresh = mock_refresh
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=None)
    
    return db

# -------------------------------------------------------------
# 1. Embedding and Vector Store Tests
# -------------------------------------------------------------

def test_embedding_generation(mock_sentence_transformer):
    texts = ["Hello world", "AegisAI platform"]
    embeddings = EmbeddingService.embed_texts(texts, batch_size=32)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    mock_sentence_transformer.encode.assert_called_once_with(
        texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True
    )

def test_chromadb_persistence(mock_chroma_client):
    ids = ["chunk_1"]
    embeddings = [[0.1] * 384]
    documents = ["test text"]
    metadatas = [{"document_id": 1}]
    
    VectorService.upsert_chunks(ids, embeddings, documents, metadatas)
    mock_chroma_client.upsert.assert_called_once_with(
        ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
    )
    
    VectorService.delete_document_vectors(1)
    mock_chroma_client.delete.assert_called_once_with(where={"document_id": 1})

# -------------------------------------------------------------
# 2. Indexing Service Tests
# -------------------------------------------------------------

@pytest.mark.anyio
async def test_indexing_service_success(mock_db, mock_chroma_client):
    mock_doc = Document()
    mock_doc.id = 42
    mock_doc.original_filename = "test.pdf"
    mock_doc.checksum = "hash123"
    mock_doc.created_at = datetime.now(timezone.utc)
    
    mock_chunk = DocumentChunk()
    mock_chunk.id = 100
    mock_chunk.document_id = 42
    mock_chunk.chunk_index = 0
    mock_chunk.page_number = 1
    mock_chunk.content = "Chunk content"
    mock_chunk.embedding_status = ChunkEmbeddingStatus.PENDING
    
    mock_execute_results = [
        MagicMock(scalar_one_or_none=lambda: mock_doc),
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_chunk]))
    ]
    mock_db.execute.side_effect = mock_execute_results
    
    with patch("app.indexing.indexing_service.AsyncSessionLocal", return_value=mock_db):
        await IndexingService.index_document(42)
        
    assert mock_chunk.embedding_status == ChunkEmbeddingStatus.INDEXED
    assert mock_chunk.embedded_at is not None
    mock_chroma_client.upsert.assert_called_once()

@pytest.mark.anyio
async def test_indexing_service_failure(mock_db, mock_sentence_transformer):
    mock_doc = Document()
    mock_doc.id = 42
    mock_doc.original_filename = "test.pdf"
    mock_doc.checksum = "hash123"
    mock_doc.created_at = datetime.now(timezone.utc)
    
    mock_chunk = DocumentChunk()
    mock_chunk.id = 100
    mock_chunk.document_id = 42
    mock_chunk.chunk_index = 0
    mock_chunk.page_number = 1
    mock_chunk.content = "Chunk content"
    mock_chunk.embedding_status = ChunkEmbeddingStatus.PENDING
    
    mock_execute_results = [
        MagicMock(scalar_one_or_none=lambda: mock_doc),
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_chunk]))
    ]
    mock_db.execute.side_effect = mock_execute_results
    
    mock_sentence_transformer.encode.side_effect = Exception("Embedding model error")
    
    with patch("app.indexing.indexing_service.AsyncSessionLocal", return_value=mock_db):
        with pytest.raises(Exception, match="Embedding model error"):
            await IndexingService.index_document(42)
            
    assert mock_chunk.embedding_status == ChunkEmbeddingStatus.FAILED

# -------------------------------------------------------------
# 3. Background Workers and Endpoints Tests
# -------------------------------------------------------------

@patch("app.workers.tasks.IndexingService.index_document", new_callable=AsyncMock)
def test_celery_indexing_task(mock_index_document):
    result = generate_embeddings(42)
    assert result["status"] == "success"
    assert result["document_id"] == 42
    mock_index_document.assert_called_once_with(42)

def test_embedding_status_endpoint(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_doc = Document()
    mock_doc.id = 42
    mock_doc.account_id = mock_account.id
    
    mock_execute_results = [
        MagicMock(scalar_one_or_none=lambda: mock_doc),
        MagicMock(all=lambda: [(ChunkEmbeddingStatus.INDEXED, 3), (ChunkEmbeddingStatus.PROCESSING, 1)])
    ]
    mock_db.execute.side_effect = mock_execute_results
    
    response = client.get("/api/v1/documents/42/embedding-status")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == 42
    assert data["status"] == "PROCESSING"
    assert data["total_chunks"] == 4
    assert data["indexed_chunks"] == 3
    assert data["failed_chunks"] == 0

def test_statistics_endpoint(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_doc = Document()
    mock_doc.id = 42
    mock_doc.account_id = mock_account.id
    mock_doc.created_at = datetime(2026, 7, 22, 12, 0, 0, tzinfo=timezone.utc)
    
    mock_execute_results = [
        MagicMock(scalar_one_or_none=lambda: mock_doc),
        MagicMock(one=lambda: (
            5, 
            4, 
            0, 
            datetime(2026, 7, 22, 12, 5, 30, tzinfo=timezone.utc)
        ))
    ]
    mock_db.execute.side_effect = mock_execute_results
    
    response = client.get("/api/v1/documents/42/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_chunks"] == 5
    assert data["indexed_chunks"] == 4
    assert data["failed_chunks"] == 0
    assert data["embedding_model"] == "BAAI/bge-small-en-v1.5"
    assert data["indexing_duration"] == 330.0
    assert data["vector_collection"] == "documents"
