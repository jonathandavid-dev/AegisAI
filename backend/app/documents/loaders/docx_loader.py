import docx
from typing import List, Tuple
from app.documents.loaders.base_loader import BaseLoader
from app.core.logging import app_logger

class DocxLoader(BaseLoader):
    """DOCX loader utilizing python-docx to extract paragraph text structures."""
    
    def load(self, file_path: str) -> List[Tuple[str, int]]:
        try:
            doc = docx.Document(file_path)
            # Collect all paragraph text segments
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paragraphs)
            app_logger.info("docx_loader_success", file_path=file_path)
            # DOCX does not expose native page markers easily; load as single page 1 context
            return [(full_text, 1)]
        except Exception as exc:
            app_logger.error("docx_loader_failed", file_path=file_path, error=str(exc))
            raise exc
