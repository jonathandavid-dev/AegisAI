from typing import List, Tuple
from app.documents.loaders.base_loader import BaseLoader
from app.core.logging import app_logger

class TxtLoader(BaseLoader):
    """Plain text loader reading files safely using UTF-8 codecs."""
    
    def load(self, file_path: str) -> List[Tuple[str, int]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            app_logger.info("txt_loader_success", file_path=file_path)
            return [(text, 1)]
        except Exception as exc:
            app_logger.error("txt_loader_failed", file_path=file_path, error=str(exc))
            raise exc
