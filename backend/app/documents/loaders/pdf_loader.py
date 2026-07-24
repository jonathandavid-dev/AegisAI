import fitz  # PyMuPDF
from typing import List, Tuple
from app.documents.loaders.base_loader import BaseLoader
from app.core.logging import app_logger

class PDFLoader(BaseLoader):
    """PDF loader utilizing PyMuPDF (fitz) to extract text page-by-page."""
    
    def load(self, file_path: str) -> List[Tuple[str, int]]:
        pages: List[Tuple[str, int]] = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                # page number is 1-indexed
                pages.append((text, page_num + 1))
            doc.close()
            app_logger.info("pdf_loader_success", file_path=file_path, pages_count=len(pages))
        except Exception as exc:
            app_logger.error("pdf_loader_failed", file_path=file_path, error=str(exc))
            raise exc
        return pages
