import re
import unicodedata

class QueryService:
    """Service responsible for query normalization and sanitation."""
    
    @staticmethod
    def normalize_query(query: str) -> str:
        """Normalizes unicode characters, simplifies whitespaces, and sanitizes punctuation."""
        if not query:
            return ""
            
        # 1. Unicode NFKC Normalization
        query = unicodedata.normalize("NFKC", query)
        
        # 2. Whitespace simplification
        query = re.sub(r"\s+", " ", query).strip()
        
        # 3. Collapse repeating punctuation sequences (e.g. !!! -> !)
        query = re.sub(r"([!?,.:;])\1+", r"\1", query)
        
        # 4. Remove matching outer quotation wraps if present
        if len(query) > 1:
            if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
                query = query[1:-1].strip()
                
        return query
