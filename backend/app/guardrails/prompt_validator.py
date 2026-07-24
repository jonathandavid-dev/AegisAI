import re
from app.core.logging import app_logger

class PromptValidator:
    """
    Validates user prompts prior to LLM submission, scanning for prompt injections,
    size limits, and policy violations.
    """
    INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"system\s+prompt\s+override",
        r"you\s+are\s+now\s+a",
        r"new\s+role\s+for\s+you",
        r"bypass\s+restrictions",
        r"do\s+not\s+follow\s+any\s+instructions",
        r"forget\s+what\s+you\s+were\s+told"
    ]

    @classmethod
    def validate_prompt(cls, prompt: str, max_chars: int = 4000) -> dict:
        """
        Validates the prompt content and size.
        """
        if not prompt or not prompt.strip():
            return {
                "success": False,
                "reason": "Empty prompt",
                "injection_detected": False,
                "details": "Prompt content is empty."
            }

        if len(prompt) > max_chars:
            return {
                "success": False,
                "reason": f"Prompt length exceeds limit of {max_chars} characters",
                "injection_detected": False,
                "details": f"Length: {len(prompt)} characters."
            }

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, prompt.lower()):
                app_logger.warning("prompt_injection_detected", prompt=prompt)
                return {
                    "success": False,
                    "reason": "Prompt contains potential adversarial prompt injection pattern",
                    "injection_detected": True,
                    "details": f"Matched pattern: '{pattern}'."
                }

        return {
            "success": True,
            "reason": None,
            "injection_detected": False,
            "details": "Prompt passed security and formatting checks."
        }
