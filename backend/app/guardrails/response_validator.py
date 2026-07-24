from app.guardrails.safety_validator import SafetyValidator

class ResponseValidator:
    """
    Validates generated response answers prior to delivery using SafetyValidator.
    """
    @classmethod
    def validate_response(cls, answer: str) -> dict:
        """
        Validates the generated response.
        """
        return SafetyValidator.validate_text(answer)
