import re
import unicodedata

class TextCleaner:
    """Utility class offering text cleaning and normalization routines for chunking operations."""
    
    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans and normalizes raw text while preserving formatting/meaning.
        1. Unicode normalization (NFKC)
        2. Replaces tabs with spaces
        3. Strips trailing line whitespaces
        4. Normalizes multiple blank lines to a single blank line
        5. Normalizes multiple consecutive spaces to a single space
        """
        if not text:
            return ""
            
        # 1. Normalize unicode sequences (NFKC)
        cleaned = unicodedata.normalize("NFKC", text)
        
        # 2. Replace tabs with 4 spaces
        cleaned = cleaned.replace("\t", "    ")
        
        # 3. Process line-by-line
        lines = [line.rstrip() for line in cleaned.splitlines()]
        
        normalized_lines = []
        consecutive_blanks = 0
        for line in lines:
            if not line:
                consecutive_blanks += 1
                if consecutive_blanks <= 1:
                    normalized_lines.append("")
            else:
                consecutive_blanks = 0
                # 5. Normalize multiple consecutive spaces
                line = re.sub(r" +", " ", line)
                normalized_lines.append(line)
                
        cleaned = "\n".join(normalized_lines)
        return cleaned.strip()
