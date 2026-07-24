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
from app.tools.registry import ToolRegistry
from app.tools.builtin.calculator_tool import CalculatorTool
from app.tools.builtin.datetime_tool import DateTimeTool
from app.tools.builtin.search_tool import SearchTool
from app.tools.builtin.document_lookup_tool import DocumentLookupTool
from app.tools.safety_guard import SafetyGuard
from app.tools.tool_executor import ToolExecutor
from app.agents.intent_detector import IntentDetector
from app.agents.planner import Planner
from app.agents.execution_context import ExecutionContext
from app.agents.orchestrator import Orchestrator
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
    account.username = "agentuser"
    account.email = "agent@example.com"
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
# 1. Tool Registry & Built-in Tools
# -------------------------------------------------------------

def test_tool_registry():
    ToolRegistry.clear()
    assert len(ToolRegistry.list_tools()) == 0
    
    ToolRegistry.register_builtin_tools()
    assert len(ToolRegistry.list_tools()) == 4
    assert ToolRegistry.get_tool("calculator") is not None
    assert ToolRegistry.get_tool("datetime") is not None

def test_calculator_tool():
    calc = CalculatorTool()
    assert calc.validate({"expression": "12 + 34"}) is True
    assert calc.validate({}) is False
    
    res = calc.execute({"expression": "150 * 0.12"})
    assert res["result"] == 18.0
    
    with pytest.raises(ValueError):
        calc.execute({"expression": "__import__('os').system('ls')"})

def test_datetime_tool():
    dt = DateTimeTool()
    res = dt.execute({})
    assert "iso" in res
    assert "formatted" in res
    assert "UTC" in res["formatted"]

# -------------------------------------------------------------
# 2. Intent Detection & Planning
# -------------------------------------------------------------

def test_intent_detection():
    i_calc = IntentDetector.detect_intent("Calculate 18% of 14500")
    assert i_calc["intent"] == "TOOL"
    assert i_calc["tool_required"] == "calculator"
    
    i_time = IntentDetector.detect_intent("What is the current server time?")
    assert i_time["intent"] == "TOOL"
    assert i_time["tool_required"] == "datetime"
    
    i_lookup = IntentDetector.detect_intent("look up section in handbook.pdf")
    assert i_lookup["intent"] == "HYBRID"
    assert i_lookup["tool_required"] == "document_lookup"
    
    i_ret = IntentDetector.detect_intent("What is our corporate password policy?")
    assert i_ret["intent"] == "RETRIEVAL"
    
    i_conv = IntentDetector.detect_intent("Hello assistant!")
    assert i_conv["intent"] == "CONVERSATION"

def test_planner():
    p_calc = Planner.generate_plan(
        "Calculate 18% of 14500", 
        {"tool_required": "calculator"}
    )
    assert p_calc["parameters"]["expression"] == "18 * 0.01 * 14500"
    
    p_lookup = Planner.generate_plan(
        "look up details in policy_document.pdf", 
        {"tool_required": "document_lookup"}
    )
    assert p_lookup["parameters"]["filename"] == "policy_document.pdf"
    assert "details" in p_lookup["parameters"]["query"]

# -------------------------------------------------------------
# 3. Safety Guard & Executor
# -------------------------------------------------------------

def test_safety_guard():
    calc = CalculatorTool()
    
    with pytest.raises(ValueError):
        SafetyGuard.validate_execution(calc, {})
        
    with pytest.raises(TypeError):
        SafetyGuard.validate_execution(calc, {"expression": 123})
        
    with pytest.raises(PermissionError):
        SafetyGuard.validate_execution(calc, {"expression": "2+2"}, user_permissions=["write_only"])

def test_tool_executor():
    calc = CalculatorTool()
    res = ToolExecutor.execute_tool(calc, {"expression": "100 / 4"})
    assert res["status"] == "success"
    assert res["result"]["result"] == 25.0
    assert "execution_time_ms" in res
    assert res["serialized"] is not None

# -------------------------------------------------------------
# 4. Orchestrator & Chat Service Integrations
# -------------------------------------------------------------

def test_orchestration_pipeline():
    ctx = ExecutionContext(account_id=1, permissions=["read"])
    res = Orchestrator.execute_orchestration("Calculate 100 * 5", ctx)
    assert res["intent"] == "TOOL"
    assert res["tool_execution"]["status"] == "success"
    assert res["tool_execution"]["result"]["result"] == 500.0

@pytest.mark.asyncio
@patch("app.search.search_service.SearchService.search")
async def test_chat_service_with_tool(mock_search, mock_db):
    mock_search.return_value = {"results": []}
    
    conv = Conversation(id=2, account_id=1, title="Agent Tool Session")
    
    with patch("app.chat.session_manager.SessionManager.get_or_create_session", return_value=conv), \
         patch("app.storage.conversation_repository.ConversationRepository.create_message") as mock_msg, \
         patch("app.llm.llm_client.LLMClient.generate", return_value="The calculation of 100*5 equals 500."):
         
        response = await ChatService.answer_question(
            db=mock_db,
            question="Calculate 100 * 5",
            account_id=1,
            conversation_id=2,
            top_k=5
        )
        
    assert response["conversation_id"] == 2
    assert "500" in response["answer"]
    assert response["tool_execution"] is not None
    assert response["tool_execution"]["tool_used"] == "calculator"
    assert response["tool_execution"]["status"] == "success"
