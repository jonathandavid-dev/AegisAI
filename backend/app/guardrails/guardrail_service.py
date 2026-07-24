from app.config.settings import settings
from app.guardrails.prompt_validator import PromptValidator
from app.guardrails.response_validator import ResponseValidator
from app.guardrails.citation_validator import CitationValidator
from app.guardrails.hallucination_detector import HallucinationDetector

class GuardrailService:
    """
    Orchestration layer that validates prompt and response quality before final delivery.
    """
    @classmethod
    def check_prompt(cls, prompt: str) -> dict:
        """
        Runs validation checks on the user prompt query.
        """
        if not settings.ENABLE_GUARDRAILS:
            return {"success": True, "reason": None, "details": "Guardrails disabled"}
        
        return PromptValidator.validate_prompt(prompt)

    @classmethod
    def check_response(cls, answer: str, citations: list, context_chunks: list[str]) -> dict:
        """
        Validates the generated response for leaks, broken citations, and hallucinated claims.
        """
        if not settings.ENABLE_GUARDRAILS:
            return {
                "success": True,
                "reason": None,
                "citation_check": {"success": True},
                "hallucination_check": {"hallucinated": False, "score": 0.0},
                "details": "Guardrails disabled"
            }

        resp_check = ResponseValidator.validate_response(answer)
        if not resp_check["success"]:
            return {
                "success": False,
                "reason": resp_check["reason"],
                "citation_check": {"success": False, "broken_citations": [], "fabricated_citations": [], "duplicate_citations": []},
                "hallucination_check": {"hallucinated": True, "score": 1.0, "fabricated_numbers": [], "fabricated_entities": [], "unsupported_sentences": []},
                "details": resp_check["details"]
            }

        cit_check = CitationValidator.validate_citations(answer, citations)
        if not cit_check["success"]:
            return {
                "success": False,
                "reason": "Broken or fabricated citations detected in response",
                "citation_check": cit_check,
                "hallucination_check": {"hallucinated": False, "score": 0.0, "fabricated_numbers": [], "fabricated_entities": [], "unsupported_sentences": []},
                "details": cit_check["details"]
            }

        hall_check = HallucinationDetector.detect_hallucinations(answer, context_chunks)
        if hall_check["score"] > settings.MAX_HALLUCINATION_SCORE:
            return {
                "success": False,
                "reason": f"Response exceeded maximum allowed hallucination threshold ({settings.MAX_HALLUCINATION_SCORE})",
                "citation_check": cit_check,
                "hallucination_check": hall_check,
                "details": hall_check["details"]
            }

        return {
            "success": True,
            "reason": None,
            "citation_check": cit_check,
            "hallucination_check": hall_check,
            "details": "All guardrails passed successfully."
        }
