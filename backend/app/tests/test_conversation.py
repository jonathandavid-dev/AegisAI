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
from app.models.conversation import Conversation, Message, MessageRole
from app.storage.conversation_repository import ConversationRepository
from app.conversation.query_rewriter import QueryRewriter
from app.conversation.summarizer import ConversationSummarizer
from app.conversation.memory_service import MemoryService
from app.conversation.history_service import HistoryService
from app.chat.chat_service import ChatService
from app.config.settings import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_account():
    account = Account()
    account.id = 1
    account.username = "testuser"
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
# 1. Unit Tests for Services
# -------------------------------------------------------------

def test_query_rewriter():
    msg1 = Message(id=1, conversation_id=1, role=MessageRole.USER, content="When was the policy updated?")
    msg2 = Message(id=2, conversation_id=1, role=MessageRole.ASSISTANT, content="It was updated in 2026.")
    
    with patch("app.llm.llm_client.LLMClient.generate") as mock_gen:
        mock_gen.return_value = "What is the update date of the policy?"
        res = QueryRewriter.rewrite_query([msg1, msg2], "What about password length?")
        assert res == "What is the update date of the policy?"
        mock_gen.assert_called_once()

def test_conversation_summarizer():
    msg = Message(id=1, conversation_id=1, role=MessageRole.USER, content="Let's talk about corporate safety.")
    
    with patch("app.llm.llm_client.LLMClient.generate") as mock_gen:
        mock_gen.return_value = "This conversation is about corporate safety."
        summary = ConversationSummarizer.generate_summary([msg], existing_summary=None)
        assert summary == "This conversation is about corporate safety."

@pytest.mark.asyncio
async def test_memory_budget_enforcement(mock_db):
    conv = Conversation(id=1, account_id=1, title="Test Session", summary=None)
    
    # 10 history messages
    history = [
        Message(id=i, conversation_id=1, role=MessageRole.USER, content=f"Msg {i}")
        for i in range(1, 11)
    ]
    
    with patch("app.conversation.summarizer.ConversationSummarizer.generate_summary") as mock_sum:
        mock_sum.return_value = "Summary of older topics."
        
        # Enforce budget of 8 messages
        summary, active_history = await MemoryService.manage_memory(mock_db, conv, history, max_history=8)
        
        assert summary == "Summary of older topics."
        assert len(active_history) == 8
        assert active_history[0].content == "Msg 3"
        assert active_history[-1].content == "Msg 10"
        
        assert conv.summary == "Summary of older topics."
        mock_db.commit.assert_called_once()

def test_history_formatter():
    messages = [
        Message(id=1, conversation_id=1, role=MessageRole.USER, content="Hello"),
        Message(id=2, conversation_id=1, role=MessageRole.ASSISTANT, content="Hi there"),
    ]
    formatted = HistoryService.format_history_for_prompt(messages)
    assert formatted == "USER: Hello\nASSISTANT: Hi there"

# -------------------------------------------------------------
# 2. Integration & REST API Endpoint Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.search.search_service.SearchService.search")
async def test_chat_service_continuation(mock_search, mock_db):
    mock_search.return_value = {"results": []}
    
    conv = Conversation(id=1, account_id=1, title="Active RAG Session")
    
    with patch("app.chat.session_manager.SessionManager.get_or_create_session", return_value=conv), \
         patch("app.conversation.conversation_service.ConversationService.prepare_context") as mock_prep, \
         patch("app.storage.conversation_repository.ConversationRepository.create_message") as mock_msg, \
         patch("app.llm.llm_client.LLMClient.generate", return_value="Mock Answer"):
         
        mock_prep.return_value = {
            "conversation_id": 1,
            "original_query": "What is the policy?",
            "rewritten_query": "What is the policy?",
            "summary": None,
            "active_history": []
        }
        
        response = await ChatService.answer_question(
            db=mock_db,
            question="What is the policy?",
            account_id=1,
            conversation_id=1,
            top_k=5
        )
        
        assert response["conversation_id"] == 1
        assert response["answer"] == "Mock Answer"
        assert response["memory"]["summary_used"] is False
        assert mock_msg.call_count == 2

def test_conversation_endpoints(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    conv = Conversation(
        id=5, 
        account_id=1, 
        title="Test Session", 
        summary="Summary text",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # 1. GET /conversations list mock
    async def mock_list(*args, **kwargs):
        return [conv]
    with patch("app.storage.conversation_repository.ConversationRepository.list_conversations", side_effect=mock_list):
        response = client.get("/api/v1/conversations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 5
        assert data[0]["title"] == "Test Session"

    # 2. GET /conversations/{id} detail mock
    async def mock_get(*args, **kwargs):
        return conv
    with patch("app.storage.conversation_repository.ConversationRepository.get_conversation", side_effect=mock_get):
        response = client.get("/api/v1/conversations/5")
        assert response.status_code == 200
        assert response.json()["id"] == 5

    # 3. PATCH /conversations/{id} rename mock
    async def mock_rename(*args, **kwargs):
        conv.title = "Renamed Session"
        return conv
    with patch("app.storage.conversation_repository.ConversationRepository.rename_conversation", side_effect=mock_rename):
        response = client.patch("/api/v1/conversations/5", json={"title": "Renamed Session"})
        assert response.status_code == 200
        assert response.json()["title"] == "Renamed Session"

    # 4. DELETE /conversations/{id} delete mock
    async def mock_delete(*args, **kwargs):
        return True
    with patch("app.storage.conversation_repository.ConversationRepository.delete_conversation", side_effect=mock_delete):
        response = client.delete("/api/v1/conversations/5")
        assert response.status_code == 200
        assert response.json()["success"] is True
