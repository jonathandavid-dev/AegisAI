import sys
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.models.document import Document, DocumentStatus
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
    account.email = "testuser@corporate.com"
    account.is_active = True
    return account

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    
    async def mock_refresh(instance):
        from datetime import datetime, timezone
        if hasattr(instance, "id") and not instance.id:
            instance.id = 1
        if hasattr(instance, "created_at") and not instance.created_at:
            instance.created_at = datetime.now(timezone.utc)
        if hasattr(instance, "updated_at") and not instance.updated_at:
            instance.updated_at = datetime.now(timezone.utc)
            
    db.refresh = mock_refresh
    db.delete = AsyncMock()
    return db

def test_upload_document_success(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    file_content = b"This is a valid corporate text document."
    import hashlib
    expected_checksum = hashlib.sha256(file_content).hexdigest()
    
    with patch("os.makedirs"), \
         patch("builtins.open", MagicMock()), \
         patch("app.workers.tasks.process_document.delay") as mock_celery:
         
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test_doc.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test_doc.txt"
        assert data["file_extension"] == "txt"
        assert data["mime_type"] == "text/plain"
        assert data["checksum"] == expected_checksum
        assert data["status"] == "QUEUED"  # Immediately transitions to QUEUED upon task queuing
        assert data["account_id"] == 1
        
        assert mock_db.add.call_count >= 1
        # db.commit called at least twice (including audit logging)
        assert mock_db.commit.call_count >= 2
        mock_celery.assert_called_once()

    app.dependency_overrides.clear()

def test_upload_document_unauthorized():
    # Attempt upload without mock credentials override or headers
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("unauth.txt", b"secret data", "text/plain")}
    )
    assert response.status_code == 401

def test_upload_document_invalid_extension(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.exe", b"binary payload", "application/octet-stream")}
    )
    # Extension exe is not allowed
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]

    app.dependency_overrides.clear()

def test_upload_document_invalid_mime(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"text payload", "image/png")}
    )
    # MIME image/png is rejected
    assert response.status_code == 400
    assert "Unsupported MIME type" in response.json()["detail"]

    app.dependency_overrides.clear()

def test_upload_document_empty_file(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

    app.dependency_overrides.clear()

def test_upload_document_too_large(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Temporarily set max size to 1 micro-MB (about 1 byte) for test
    with patch.object(settings, "MAX_UPLOAD_SIZE_MB", 0.000001):
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("large.txt", b"this string exceeds 5 bytes", "text/plain")}
        )
        assert response.status_code == 413
        assert "exceeds maximum" in response.json()["detail"]

def test_list_documents(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_doc = Document()
    mock_doc.id = 42
    mock_doc.account_id = mock_account.id
    mock_doc.original_filename = "test.pdf"
    mock_doc.stored_filename = "uuid.pdf"
    mock_doc.file_extension = "pdf"
    mock_doc.mime_type = "application/pdf"
    mock_doc.file_size = 1024
    mock_doc.storage_path = "/path/uuid.pdf"
    mock_doc.checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    mock_doc.status = DocumentStatus.UPLOADED
    from datetime import datetime, timezone
    mock_doc.created_at = datetime.now(timezone.utc)
    mock_doc.updated_at = datetime.now(timezone.utc)
    
    # Mocking sqlalchemy execute return
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value.all.return_value = [mock_doc]
    mock_db.execute = AsyncMock(return_value=mock_execute_result)

    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 42
    assert data[0]["original_filename"] == "test.pdf"

    app.dependency_overrides.clear()

def test_delete_document_success(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_doc = Document()
    mock_doc.id = 42
    mock_doc.account_id = mock_account.id
    mock_doc.storage_path = "/path/uuid.pdf"

    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_doc
    mock_db.execute = AsyncMock(return_value=mock_execute_result)

    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
         
        response = client.delete("/api/v1/documents/42")
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_remove.assert_called_once_with("/path/uuid.pdf")
        mock_db.delete.assert_called_once_with(mock_doc)
        assert mock_db.commit.call_count >= 1

    app.dependency_overrides.clear()

def test_delete_document_not_found(mock_account, mock_db):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_execute_result)

    response = client.delete("/api/v1/documents/99")
    assert response.status_code == 404

    app.dependency_overrides.clear()
