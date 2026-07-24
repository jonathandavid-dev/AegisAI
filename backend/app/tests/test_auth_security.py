import sys
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.auth.password_service import PasswordService
from app.auth.jwt_service import JWTService
from app.auth.token_service import TokenService
from app.auth.auth_service import AuthService
from app.accounts.account_service import AccountService
from app.security.permissions import PermissionChecker
from app.security.decorators import require_roles
from app.models.account import Account
from app.models.conversation import Conversation
from app.models.document import Document
from app.audit.audit_service import AuditService

@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db

# -------------------------------------------------------------
# 1. Password Hashing & Complexity Checks
# -------------------------------------------------------------

def test_password_complexity():
    assert PasswordService.is_complex("ValidPass123!") is True
    assert PasswordService.is_complex("short") is False
    assert PasswordService.is_complex("NoSpecialChar123") is False
    assert PasswordService.is_complex("nouppercase123!") is False
    assert PasswordService.is_complex("NONUMBERCHARS!") is False

def test_password_hashing():
    pwd = "MySecretPassWord789!"
    hashed = PasswordService.hash_password(pwd)
    assert hashed != pwd
    assert PasswordService.verify_password(pwd, hashed) is True
    assert PasswordService.verify_password("wrong", hashed) is False

# -------------------------------------------------------------
# 2. JWT Generation & Decoding Claims
# -------------------------------------------------------------

def test_jwt_claims():
    data = {"sub": "123", "username": "adminuser", "role": "ADMIN"}
    token = JWTService.create_access_token(data)
    decoded = JWTService.decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "123"
    assert decoded["username"] == "adminuser"
    assert decoded["role"] == "ADMIN"
    assert "exp" in decoded

# -------------------------------------------------------------
# 3. RBAC Permission Checks
# -------------------------------------------------------------

def test_role_permission_checker():
    # Admin User
    admin = Account(username="admin", role="ADMIN")
    # Editor User
    editor = Account(username="editor", role="EDITOR")
    # Viewer User
    viewer = Account(username="viewer", role="VIEWER")
    
    # 1. document:upload permission -> ADMIN, EDITOR
    checker_upload = PermissionChecker("document:upload")
    assert checker_upload(admin) == admin
    assert checker_upload(editor) == editor
    with pytest.raises(HTTPException) as exc_info:
        checker_upload(viewer)
    assert exc_info.value.status_code == 403

    # 2. document:delete permission -> ADMIN
    checker_delete = PermissionChecker("document:delete")
    assert checker_delete(admin) == admin
    with pytest.raises(HTTPException) as exc_info:
        checker_delete(editor)
    assert exc_info.value.status_code == 403

# -------------------------------------------------------------
# 4. Resource Ownership Verification
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_repository_conversation_ownership(mock_db):
    from app.storage.conversation_repository import ConversationRepository
    
    # Mock database return for conversation belonging to account_id = 1
    conv = Conversation(id=10, account_id=1, title="User Conversation")
    
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = conv
    mock_db.execute = AsyncMock(return_value=mock_res)
    
    # Get conversation with matching owner -> Succeeds
    res = await ConversationRepository.get_conversation(mock_db, 10, account_id=1)
    assert res == conv
    
    # Get conversation with different owner -> Fails
    mock_res.scalar_one_or_none.return_value = None
    res = await ConversationRepository.get_conversation(mock_db, 10, account_id=2)
    assert res is None

# -------------------------------------------------------------
# 5. Audit Logging Integrations
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_service(mock_db):
    with patch("app.audit.audit_repository.AuditRepository.create_audit_log") as mock_repo_log:
        mock_repo_log.return_value = MagicMock()
        
        await AuditService.log_event(
            db=mock_db,
            account_id=1,
            action="LOGIN",
            resource="account",
            resource_id="1",
            ip_address="127.0.0.1"
        )
        
        mock_repo_log.assert_called_once()
        args, kwargs = mock_repo_log.call_args
        assert kwargs["account_id"] == 1
        assert kwargs["action"] == "LOGIN"
        assert kwargs["ip_address"] == "127.0.0.1"
