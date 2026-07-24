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
from app.models.document_chunk import DocumentChunk
from app.documents.loaders.pdf_loader import PDFLoader
from app.documents.loaders.docx_loader import DocxLoader
from app.documents.loaders.txt_loader import TxtLoader
from app.documents.cleaners.text_cleaner import TextCleaner
from app.documents.chunkers.recursive_chunker import RecursiveChunker
from app.documents.services.parsing_service import ParsingService

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()

# -------------------------------------------------------------
# 1. Loader Unit Tests
# -------------------------------------------------------------

def test_txt_loader():
    loader = TxtLoader()
    with patch("builtins.open", mock_open_helper("Hello world text content.")):
        result = loader.load("dummy.txt")
        assert len(result) == 1
        assert result[0][0] == "Hello world text content."
        assert result[0][1] == 1

def test_pdf_loader():
    loader = PDFLoader()
    # Mock PyMuPDF fitz.open and page extraction
    mock_doc = MagicMock()
    mock_page_1 = MagicMock()
    mock_page_1.get_text.return_value = "Page 1 text content."
    mock_page_2 = MagicMock()
    mock_page_2.get_text.return_value = "Page 2 text content."
    mock_doc.__len__.return_value = 2
    mock_doc.load_page.side_effect = [mock_page_1, mock_page_2]
    
    with patch("fitz.open", return_value=mock_doc):
        result = loader.load("dummy.pdf")
        assert len(result) == 2
        assert result[0][0] == "Page 1 text content."
        assert result[0][1] == 1
        assert result[1][0] == "Page 2 text content."
        assert result[1][1] == 2
        mock_doc.close.assert_called_once()

def test_docx_loader():
    loader = DocxLoader()
    # Mock python-docx paragraphs
    mock_p1 = MagicMock(text="Paragraph 1 text.")
    mock_p2 = MagicMock(text="Paragraph 2 text.")
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_p1, mock_p2]
    
    with patch("docx.Document", return_value=mock_doc):
        result = loader.load("dummy.docx")
        assert len(result) == 1
        assert "Paragraph 1 text." in result[0][0]
        assert "Paragraph 2 text." in result[0][0]
        assert result[0][1] == 1

# Helper function to mock open
def mock_open_helper(content: str):
    import io
    return lambda *args, **kwargs: io.StringIO(content)

# -------------------------------------------------------------
# 2. Text Cleaner Unit Tests
# -------------------------------------------------------------

def test_text_cleaner():
    raw_text = "Hello\tworld.\n\n\nThis  is   cleaned   text. \nUnicode: fi\u0301le\t\n"
    # Cleaner replaces tab with 4 spaces, strips line right whitespace,
    # compresses consecutive blank lines to one, and replaces multiple spaces with a single space.
    # Therefore, "Hello\tworld." -> "Hello    world." -> compressed to "Hello world."
    expected = "Hello world.\n\nThis is cleaned text.\nUnicode: fíle"
    cleaned = TextCleaner.clean(raw_text)
    assert cleaned == expected

# -------------------------------------------------------------
# 3. Recursive Chunker Unit Tests
# -------------------------------------------------------------

def test_recursive_chunker_basic():
    # Size 20, Overlap 5
    chunker = RecursiveChunker(chunk_size=20, chunk_overlap=5)
    text = "Hello world from the custom text splitter engine."
    chunks = chunker.split_text(text)
    
    # Assert segments are smaller than size boundary
    for chunk in chunks:
        assert len(chunk) <= 20
        
    # Verify split elements merge back
    assert len(chunks) > 1

# -------------------------------------------------------------
# 4. Parsing Service Unit Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_parsing_service_pipeline():
    mock_doc = Document()
    mock_doc.id = 12
    mock_doc.original_filename = "test.txt"
    mock_doc.file_extension = "txt"
    mock_doc.storage_path = "dummy.txt"
    mock_doc.status = DocumentStatus.QUEUED
    
    # Mock database session execution supporting async context managers
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)
    
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_doc
    mock_db.execute.return_value = mock_execute_result
    
    # Mock loading txt content
    with patch("app.documents.services.parsing_service.AsyncSessionLocal", return_value=mock_db), \
         patch("app.documents.loaders.txt_loader.TxtLoader.load", return_value=[("Text data for chunk parsing.", 1)]):
         
        await ParsingService.process_document_by_id(12)
        
        assert mock_doc.status == DocumentStatus.PROCESSED
        # Ensure chunks were added (db.add_all)
        mock_db.add_all.assert_called_once()
        assert mock_db.commit.call_count >= 2

# -------------------------------------------------------------
# 5. API Endpoints Unit Tests
# -------------------------------------------------------------

@pytest.fixture
def mock_account():
    acc = Account()
    acc.id = 1
    acc.email = "lead@aegis.ai"
    return acc

def test_list_document_chunks(mock_account):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    # Mock db and execute results
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    mock_doc = Document(id=1, account_id=1)
    
    mock_chunk = DocumentChunk()
    mock_chunk.id = 101
    mock_chunk.document_id = 1
    mock_chunk.chunk_index = 0
    mock_chunk.page_number = 1
    mock_chunk.content = "Mock chunk text."
    mock_chunk.character_count = 16
    from app.models.document_chunk import ChunkEmbeddingStatus
    mock_chunk.embedding_status = ChunkEmbeddingStatus.PENDING
    from datetime import datetime, timezone
    mock_chunk.created_at = datetime.now(timezone.utc)
    
    # Mocking first query (Document exists)
    mock_exec_1 = MagicMock()
    mock_exec_1.scalar_one_or_none.return_value = mock_doc
    # Mocking second query (Chunks list)
    mock_exec_2 = MagicMock()
    mock_exec_2.scalars.return_value.all.return_value = [mock_chunk]
    
    mock_db.execute.side_effect = [mock_exec_1, mock_exec_2]
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.get("/api/v1/documents/1/chunks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Mock chunk text."
    assert data[0]["chunk_index"] == 0

    app.dependency_overrides.clear()

def test_preview_document(mock_account):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    mock_doc = Document(id=1, account_id=1, original_filename="test.pdf", file_extension="pdf")
    
    # Mocking query calls: 1. Fetch document, 2. Count chunks, 3. Max page_number, 4. Get first chunk
    mock_exec_doc = MagicMock()
    mock_exec_doc.scalar_one_or_none.return_value = mock_doc
    
    mock_exec_count = MagicMock()
    mock_exec_count.scalar_one.return_value = 5
    
    mock_exec_page = MagicMock()
    mock_exec_page.scalar_one.return_value = 2
    
    mock_chunk = DocumentChunk(content="First chunk text preview contents.")
    mock_exec_chunk = MagicMock()
    mock_exec_chunk.scalar_one_or_none.return_value = mock_chunk
    
    mock_db.execute.side_effect = [mock_exec_doc, mock_exec_count, mock_exec_page, mock_exec_chunk]
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.get("/api/v1/documents/1/preview")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["page_count"] == 2
    assert data["total_chunks"] == 5
    assert "First chunk text" in data["preview_content"]

    app.dependency_overrides.clear()
