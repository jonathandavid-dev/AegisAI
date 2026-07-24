import re

class CitationValidator:
    """
    Validates references and citations in LLM responses to ensure alignment with grounding documents.
    """
    @staticmethod
    def validate_citations(answer: str, citations: list) -> dict:
        """
        Validates the citations present in the generated answer against the retrieved chunk context.
        """
        # Find all citations of the form [1], [2], [10] etc.
        matches = re.findall(r"\[([0-9]+)\]", answer)
        citation_indices = [int(m) for m in matches]
        
        broken = []
        fabricated = []
        duplicates = []
        
        num_citations = len(citations)
        for idx in citation_indices:
            if idx <= 0 or idx > num_citations:
                broken.append(f"[{idx}]")
                fabricated.append(f"[{idx}]")
            else:
                # Check if citation object matches retrieved chunk context
                cit_obj = citations[idx - 1]
                if not cit_obj.get("text") or not cit_obj.get("filename"):
                    broken.append(f"[{idx}]")
        
        # Check duplicate adjacent citations, e.g. [1][1] or [1] [1]
        adj_matches = re.findall(r"\[([0-9]+)\]\s*\[\1\]", answer)
        for dup in adj_matches:
            duplicates.append(f"[{dup}]")
            
        success = len(broken) == 0 and len(fabricated) == 0
        
        return {
            "success": success,
            "broken_citations": broken,
            "fabricated_citations": fabricated,
            "duplicate_citations": list(set(duplicates)),
            "details": f"Validated {len(citation_indices)} citations. Broken: {len(broken)}, Fabricated: {len(fabricated)}, Duplicates: {len(duplicates)}."
        }
