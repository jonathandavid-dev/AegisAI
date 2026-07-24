import re

class SafetyValidator:
    """
    Scans input or output text for secrets, profanity, empty data, or length issues.
    """
    UNSAFE_PATTERNS = [
        r"aws_key|aws_secret|api_key|client_secret",
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"db_password|postgres_password",
        r"internal\s+server\s+error\s+at\s+[\d\.]+",
        r"stack\s+trace|traceback\b"
    ]

    PROFANITY_LIST = [
        "badword1", "badword2", "fuck", "shit", "bitch", "asshole"
    ]

    MAX_RESPONSE_LENGTH = 10000

    @classmethod
    def validate_text(cls, text: str) -> dict:
        """
        Runs validations against credentials, profanity, length, and emptyness.
        """
        if not text or not text.strip():
            return {
                "success": False,
                "reason": "Empty content detected",
                "policy_violation": True,
                "details": "Content is empty."
            }

        if len(text) > cls.MAX_RESPONSE_LENGTH:
            return {
                "success": False,
                "reason": f"Content length exceeded maximum policy limit ({cls.MAX_RESPONSE_LENGTH})",
                "policy_violation": True,
                "details": f"Length is {len(text)}."
            }

        text_lower = text.lower()
        for word in cls.PROFANITY_LIST:
            if word in text_lower:
                return {
                    "success": False,
                    "reason": "Forbidden profanity language detected",
                    "policy_violation": True,
                    "details": f"Flagged term: '{word}'."
                }

        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, text_lower):
                return {
                    "success": False,
                    "reason": "System credential leak or trace info detected",
                    "policy_violation": True,
                    "details": f"Matched pattern: '{pattern}'."
                }

        return {
            "success": True,
            "reason": None,
            "policy_violation": False,
            "details": "Passed security policies."
        }
