import sys
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.retrieval.query_service import QueryService
from app.retrieval.filters import FilterService
from app.retrieval.ranking_service import RankingService
from app.search.search_service import SearchService
from app.embeddings.embedding_service import EmbeddingService

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
    account.email = "lead@aegis.ai"
    account.hashed_password = "hashed_password"
    account.is_active = True
    account.created_at = datetime.now(timezone.utc)
    return account

# -------------------------------------------------------------
# 1. Query Preprocessing and Filters Tests
# -------------------------------------------------------------

def test_query_normalization():
    # Whitespace and Unicode
    assert QueryService.normalize_query("  Hello   \u00A0 World  ") == "Hello World"
    # Punctuation collapsing
    assert QueryService.normalize_query("Wait!!! What???") == "Wait! What?"
    # Outer quotes stripping
    assert QueryService.normalize_query('"exact search query"') == "exact search query"
    # Empty query
    assert QueryService.normalize_query("") == ""

def test_filter_compilation():
    # No filters
    assert FilterService.compile_filters({}) is None
    
    # Equality filter
    f1 = {"document_id": 42}
    assert FilterService.compile_filters(f1) == {"document_id": {"$eq": 42}}
    
    # Multiple filters
    f2 = {"filename": "test.pdf", "page_number": 3}
    assert FilterService.compile_filters(f2) == {
        "$and": [
            {"filename": {"$eq": "test.pdf"}},
            {"page_number": {"$eq": 3}}
        ]
    }
    
    # Date range filters
    f3 = {"created_after": "2026-07-22T12:00:00", "created_before": "2026-07-22T13:00:00"}
    assert FilterService.compile_filters(f3) == {
        "$and": [
            {"created_at": {"$gte": "2026-07-22T12:00:00"}},
            {"created_at": {"$lte": "2026-07-22T13:00:00"}}
        ]
    }

# -------------------------------------------------------------
# 2. Ranking and Threshold Tests
# -------------------------------------------------------------

def test_ranking_and_scores():
    chroma_mock_results = {
        "ids": [["chunk_1", "chunk_2", "chunk_3"]],
        "distances": [[0.1, 0.3, 0.4]],  # Cosine distances (similarity = 1.0 - dist)
        "documents": [["text 1", "text 2", "text 3"]],
        "metadatas": [[
            {"document_id": 1, "filename": "doc.pdf", "page_number": 1, "chunk_index": 0},
            {"document_id": 1, "filename": "doc.pdf", "page_number": 1, "chunk_index": 1},
            {"document_id": 1, "filename": "doc.pdf", "page_number": 2, "chunk_index": 2}
        ]]
    }
    
    # Threshold 0.75: chunk_3 similarity is 0.60 (distance 0.4), so it should be dropped!
    # chunk_1 score = 0.90, chunk_2 score = 0.70 (distance 0.3) which is also < 0.75, so dropped!
    results = RankingService.rank_results(chroma_mock_results, similarity_threshold=0.75)
    assert len(results) == 1
    assert results[0]["chunk_id"] == "chunk_1"
    assert results[0]["score"] == 0.90
    
    # Threshold 0.65: chunk_1 and chunk_2 should be kept, chunk_3 (score 0.60) dropped!
    results_lower = RankingService.rank_results(chroma_mock_results, similarity_threshold=0.65)
    assert len(results_lower) == 2
    assert results_lower[0]["chunk_id"] == "chunk_1"
    assert results_lower[1]["chunk_id"] == "chunk_2"
    assert results_lower[1]["score"] == 0.70

# -------------------------------------------------------------
# 3. Search Service Orchestrator Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_service_orchestration(mock_chroma_client):
    mock_chroma_client.query.return_value = {
        "ids": [["chunk_1"]],
        "distances": [[0.15]],
        "documents": [["Cleaning services content"]],
        "metadatas": [[{"document_id": 12, "filename": "cleaning.pdf", "page_number": 2, "chunk_index": 1}]]
    }
    
    res = await SearchService.search("Ask questions???", top_k=5, filters={"document_id": 12})
    assert res["query"] == "Ask questions???"
    assert len(res["results"]) == 1
    assert res["results"][0]["score"] == 0.85
    assert res["results"][0]["document_id"] == 12
    assert res["processing_time_ms"] > 0
    mock_chroma_client.query.assert_called_once()


# -------------------------------------------------------------
# 4. Search Endpoints Tests
# -------------------------------------------------------------

def test_search_endpoint(mock_account, mock_chroma_client):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    mock_chroma_client.query.return_value = {
        "ids": [["chunk_1"]],
        "distances": [[0.1]],
        "documents": [["Corporate knowledge chunk"]],
        "metadatas": [[{"document_id": 7, "filename": "corporate.docx", "page_number": 1, "chunk_index": 4}]]
    }
    
    response = client.post(
        "/api/v1/search",
        json={"query": "semantic query", "top_k": 3}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "semantic query"
    assert len(data["results"]) == 1
    assert data["results"][0]["document_id"] == 7
    assert "processing_time_ms" in data

def test_advanced_search_endpoint(mock_account, mock_chroma_client):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    mock_chroma_client.query.return_value = {
        "ids": [["chunk_1", "chunk_2"]],
        "distances": [[0.12, 0.28]],  # Scores: 0.88, 0.72
        "documents": [["first content", "second content"]],
        "metadatas": [[
            {"document_id": 8, "filename": "doc.pdf", "page_number": 1, "chunk_index": 0},
            {"document_id": 8, "filename": "doc.pdf", "page_number": 2, "chunk_index": 1}
        ]]
    }
    
    # Advanced search with lower custom threshold
    response = client.post(
        "/api/v1/search/advanced",
        json={
            "query": "adv query",
            "top_k": 10,
            "filters": {
                "similarity_threshold": 0.70,
                "filename": "doc.pdf"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2  # Both pass because threshold = 0.70
    assert data["results"][0]["score"] == 0.88
    assert data["results"][1]["score"] == 0.72

def test_empty_query_validation(mock_account):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    # Verify empty queries fail Pydantic model validation with HTTP 422
    response = client.post(
        "/api/v1/search",
        json={"query": ""}
    )
    assert response.status_code == 422
