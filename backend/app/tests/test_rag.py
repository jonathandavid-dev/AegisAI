import sys
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_account
from app.dependencies.database import get_db
from app.models.account import Account
from app.models.conversation import Conversation
from app.context.context_builder import ContextBuilder
from app.context.citation_builder import CitationBuilder
from app.llm.prompt_builder import PromptBuilder
from app.llm.providers import MockProvider, OpenAIProvider
from app.llm.llm_client import LLMClient
from app.chat.chat_service import ChatService
from app.config.settings import settings

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
        yield mock_model

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
    account.hashed_password = "hashed"
    account.is_active = True
    account.created_at = datetime.now(timezone.utc)
    return account

@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db

# -------------------------------------------------------------
# 1. Builder Utilities Tests
# -------------------------------------------------------------

def test_prompt_builder():
    context = "Source info text block"
    question = "What is the policy?"
    prompt = PromptBuilder.build_prompt(context, question)
    
    assert "SYSTEM" in prompt
    assert "CONTEXT" in prompt
    assert "QUESTION" in prompt
    assert "Answer ONLY using the supplied context." in prompt
    assert context in prompt
    assert question in prompt

def test_context_builder_budget():
    chunks = [
        {"chunk_id": "c1", "document_id": 1, "filename": "doc1.pdf", "page_number": 1, "chunk_index": 0, "content": "A" * 100},
        {"chunk_id": "c2", "document_id": 1, "filename": "doc1.pdf", "page_number": 1, "chunk_index": 1, "content": "B" * 200},
        {"chunk_id": "c3", "document_id": 2, "filename": "doc2.pdf", "page_number": 2, "chunk_index": 0, "content": "C" * 300},
    ]
    
    # 1. Max chunks budget check
    context_str, selected = ContextBuilder.build_context(chunks, max_chunks=2)
    assert len(selected) == 2
    assert "Source 1: doc1.pdf" in context_str
    assert "Source 2: doc1.pdf" in context_str
    assert "Source 3" not in context_str

    # 2. Token budget check (heuristic: 1 token = ~4 chars)
    _, selected_tokens = ContextBuilder.build_context(chunks, max_chunks=5, max_tokens=50)
    assert len(selected_tokens) == 1
    assert selected_tokens[0]["chunk_id"] == "c1"

def test_citation_builder():
    selected = [
        {"chunk_id": "c1", "document_id": 5, "filename": "policy.pdf", "page_number": 2, "chunk_index": 4, "content": "abc"},
        {"chunk_id": "c1", "document_id": 5, "filename": "policy.pdf", "page_number": 2, "chunk_index": 4, "content": "abc"},
        {"chunk_id": "c2", "document_id": 5, "filename": "policy.pdf", "page_number": 2, "chunk_index": 5, "content": "def"},
    ]
    citations = CitationBuilder.build_citations(selected)
    assert len(citations) == 2
    assert citations[0]["document_id"] == 5
    assert citations[0]["page_number"] == 2
    assert citations[0]["chunk_index"] == 4
    assert citations[1]["chunk_index"] == 5

# -------------------------------------------------------------
# 2. Providers and Client Abstractions Tests
# -------------------------------------------------------------

def test_mock_llm_provider():
    provider = MockProvider()
    
    prompt_with_context = (
        "SYSTEM\n...\n"
        "--------------------------------\n"
        "CONTEXT\n[Source 1: policy.pdf (Page 2, Chunk 4)]\nAll employees must lock screens.\n"
        "--------------------------------\n"
        "QUESTION\nWhat is screen policy?"
    )
    answer = provider.generate_text(prompt_with_context)
    assert "policy.pdf" in answer
    assert "All employees must lock screens" in answer

    prompt_empty = (
        "SYSTEM\n...\n"
        "--------------------------------\n"
        "CONTEXT\nNo context available.\n"
        "--------------------------------\n"
        "QUESTION\nWhat is screen policy?"
    )
    answer_empty = provider.generate_text(prompt_empty)
    assert "information is not available" in answer_empty

def test_llm_client_instantiation():
    with patch.object(settings, "LLM_PROVIDER", "mock"):
        LLMClient._provider = None
        provider = LLMClient.get_provider()
        assert isinstance(provider, MockProvider)

    with patch.object(settings, "LLM_PROVIDER", "openai"):
        LLMClient._provider = None
        provider = LLMClient.get_provider()
        assert isinstance(provider, OpenAIProvider)

# -------------------------------------------------------------
# 3. ChatService and Endpoints Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.search.search_service.SearchService.search")
async def test_chat_service_success(mock_search, mock_db):
    mock_search.return_value = {
        "query": "query text",
        "results": [
            {
                "chunk_id": "ch_1",
                "document_id": 9,
                "filename": "guide.pdf",
                "page_number": 3,
                "chunk_index": 12,
                "content": "This is context text detail.",
                "score": 0.85
            }
        ]
    }
    
    conv = Conversation(id=1, account_id=1, title="Test Session")
    
    with patch("app.chat.session_manager.SessionManager.get_or_create_session", return_value=conv), \
         patch("app.storage.conversation_repository.ConversationRepository.create_message") as mock_msg, \
         patch.object(settings, "LLM_PROVIDER", "mock"):
         
        LLMClient._provider = None
        response = await ChatService.answer_question(
            db=mock_db,
            question="test question",
            account_id=1,
            conversation_id=None,
            top_k=5
        )
        
    assert response["question"] == "test question"
    assert "guide.pdf" in response["answer"]
    assert len(response["citations"]) == 1
    assert response["citations"][0]["document_id"] == 9
    assert response["retrieval"]["chunks_used"] == 1
    assert response["processing_time_ms"] > 0

def test_chat_endpoint(mock_account, mock_chroma_client, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_chroma_client.query.return_value = {
        "ids": [["chunk_1"]],
        "distances": [[0.1]],
        "documents": [["Valid context doc text."]],
        "metadatas": [[{"document_id": 1, "filename": "policy.pdf", "page_number": 1, "chunk_index": 0}]]
    }
    
    conv = Conversation(id=1, account_id=1, title="Test Session")
    
    with patch("app.chat.session_manager.SessionManager.get_or_create_session", return_value=conv), \
         patch("app.storage.conversation_repository.ConversationRepository.create_message") as mock_msg, \
         patch.object(settings, "LLM_PROVIDER", "mock"):
         
        LLMClient._provider = None
        response = client.post(
            "/api/v1/chat",
            json={"question": "What is the policy?", "top_k": 5}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is the policy?"
    assert "policy.pdf" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["retrieval"]["chunks_used"] == 1
