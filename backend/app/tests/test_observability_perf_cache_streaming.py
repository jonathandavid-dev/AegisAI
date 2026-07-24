import sys
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Mock sentence transformers and chromadb immediately before importing app modules
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.dependencies.auth import get_current_account
from app.dependencies.database import get_db
from app.models.account import Account
from app.models.conversation import Conversation
from app.cache.cache_service import CacheService
from app.cache.retrieval_cache import RetrievalCache
from app.cache.embedding_cache import EmbeddingCache
from app.observability.logging import bind_observability_fields, clear_observability_fields, observability_processor
from app.observability.tracing import trace_span
from app.observability.metrics import export_metrics, track_search_latency

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_account():
    account = Account()
    account.id = 99
    account.email = "telemetry@aegis.ai"
    account.hashed_password = "hashed"
    account.is_active = True
    return account

@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    return db

# -------------------------------------------------------------
# 1. Health Endpoints Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoints(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Test overall /health
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "alive"

    # Test /health/live
    res_live = client.get("/api/v1/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    # Test /health/ready (mock dependencies checks to return True)
    with patch("app.health.health_service.HealthService.check_db", return_value=True), \
         patch("app.health.health_service.HealthService.check_redis", return_value=True), \
         patch("app.health.health_service.HealthService.check_chromadb", return_value=True), \
         patch("app.health.health_service.HealthService.check_llm", return_value=True), \
         patch("app.health.health_service.HealthService.check_celery", return_value=True):
         res_ready = client.get("/api/v1/health/ready")
         assert res_ready.status_code == 200
         data = res_ready.json()
         assert data["status"] == "ready"
         assert data["details"]["database"] == "ok"

# -------------------------------------------------------------
# 2. Caching Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_service_in_memory_fallback():
    # Force use of in-memory fallback by patching get_redis to return None
    with patch("app.cache.cache_service.CacheService.get_redis", return_value=None):
        await CacheService.set("test_key", {"data": 123}, ttl=60)
        cached = await CacheService.get("test_key")
        assert cached == {"data": 123}

        # Invalidation
        await CacheService.invalidate("test_key")
        cached_after = await CacheService.get("test_key")
        assert cached_after is None

@pytest.mark.asyncio
async def test_retrieval_and_embedding_caches():
    with patch("app.cache.cache_service.CacheService.get_redis", return_value=None):
        # 1. Retrieval Cache Set & Get (workspace-aware isolation check)
        workspace_1 = 10
        workspace_2 = 20
        query = "password policy details"
        
        await RetrievalCache.set(workspace_1, query, top_k=5, filters={}, value={"results": "workspace_10_results"})
        await RetrievalCache.set(workspace_2, query, top_k=5, filters={}, value={"results": "workspace_20_results"})
        
        val_ws1 = await RetrievalCache.get(workspace_1, query, top_k=5, filters={})
        val_ws2 = await RetrievalCache.get(workspace_2, query, top_k=5, filters={})
        
        assert val_ws1["results"] == "workspace_10_results"
        assert val_ws2["results"] == "workspace_20_results"

        # 2. Invalidation
        await RetrievalCache.invalidate_workspace(workspace_1)
        val_ws1_after = await RetrievalCache.get(workspace_1, query, top_k=5, filters={})
        val_ws2_after = await RetrievalCache.get(workspace_2, query, top_k=5, filters={})
        
        assert val_ws1_after is None
        assert val_ws2_after["results"] == "workspace_20_results"

        # 3. Embedding Cache check
        await EmbeddingCache.set(workspace_1, "text chunk content", [0.1, 0.2, 0.3])
        embed = await EmbeddingCache.get(workspace_1, "text chunk content")
        assert embed == [0.1, 0.2, 0.3]

# -------------------------------------------------------------
# 3. Observability & Logging Tests
# -------------------------------------------------------------

def test_structured_logging_processor():
    clear_observability_fields()
    bind_observability_fields(
        correlation_id="corr-1234",
        workspace_id=9,
        account_id=99,
        conversation_id=45,
        request_path="/api/v1/chat",
        duration_ms=12.50
    )
    
    event_dict = {}
    processed = observability_processor(None, "info", event_dict)
    
    assert processed["correlation_id"] == "corr-1234"
    assert processed["workspace_id"] == 9
    assert processed["account_id"] == 99
    assert processed["conversation_id"] == 45
    assert processed["request_path"] == "/api/v1/chat"
    assert processed["duration_ms"] == 12.50
    
    clear_observability_fields()

def test_tracing_context_manager():
    with patch("app.observability.tracing.settings.ENABLE_OPENTELEMETRY", False):
        # When disabled, should yield safely and run code block
        with trace_span("LLM") as span:
            assert span is None
            
        # Verify block execution works without issues
        flag = False
        with trace_span("Retrieval"):
            flag = True
        assert flag is True

# -------------------------------------------------------------
# 4. Metrics Scrape Endpoint
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_metrics_export():
    track_search_latency(0.12)
    # Patch database updater to prevent query errors during test scrape
    with patch("app.observability.metrics.update_db_metrics", AsyncMock()):
        metrics_data, content_type = await export_metrics()
        assert b"search_latency_seconds" in metrics_data
        assert b"cache_requests_total" in metrics_data

# -------------------------------------------------------------
# 5. SSE Streaming Endpoints
# -------------------------------------------------------------

def test_chat_streaming_response(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    conv = Conversation(id=77, account_id=mock_account.id, title="Stream Turn")
    
    # Mock retrieval, prompt, history operations
    with patch("app.chat.session_manager.SessionManager.get_or_create_session", return_value=conv), \
         patch("app.conversation.conversation_service.ConversationService.prepare_context", return_value={
             "rewritten_query": "hello streaming world",
             "summary": None,
             "active_history": []
         }), \
         patch("app.search.search_service.SearchService.search", return_value={"results": []}), \
         patch("app.llm.llm_client.LLMClient.generate_stream") as mock_stream_gen, \
         patch("app.storage.conversation_repository.ConversationRepository.create_message", AsyncMock()):

        # Set up async generator output mock for LLM text chunks
        async def mock_generator():
            yield "Hi "
            yield "from "
            yield "cognitive "
            yield "stream."
            
        mock_stream_gen.return_value = mock_generator()
        
        # Call streaming chat route
        response = client.post(
            "/api/v1/chat",
            json={"question": "is stream working?", "top_k": 3, "stream": True}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse streaming SSE content lines
        body = response.text
        lines = body.split("\n")
        
        progress_events = []
        tokens = []
        done_payload = None
        
        for line in lines:
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                if payload["type"] == "progress":
                    progress_events.append(payload["stage"])
                elif payload["type"] == "token":
                    tokens.append(payload["content"])
                elif payload["type"] == "done":
                    done_payload = payload
                    
        assert "start" in progress_events
        assert "llm_generation" in progress_events
        assert "".join(tokens) == "Hi from cognitive stream."
        assert done_payload is not None
        assert done_payload["conversation_id"] == 77
        assert done_payload["answer"] == "Hi from cognitive stream."
