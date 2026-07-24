from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseLoader(ABC):
    """Abstract interface defining standard loading interfaces for all document formats."""
    
    @abstractmethod
    def load(self, file_path: str) -> List[Tuple[str, int]]:
        """
        Parses document contents.
        Returns a list of tuples containing: (page_text, page_number_1_indexed).
        """
        pass
