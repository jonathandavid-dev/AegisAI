import re
import bcrypt

class PasswordService:
    """Provides secure password hashing, verification, and complexity validation using bcrypt."""
    
    @staticmethod
    def is_complex(password: str) -> bool:
        """Validates that a password satisfies enterprise complexity criteria."""
        if len(password) < 8:
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        # Matches typical special characters
        special_pattern = re.compile(r"[@_!#$%^&*()<>?/\|}{~:\-+=]")
        if not special_pattern.search(password):
            return False
        return True

    @staticmethod
    def hash_password(password: str) -> str:
        """Generates a secure salt and hashes the plaintext password."""
        salt = bcrypt.gensalt(rounds=12)
        hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_bytes.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verifies a candidate password against the database bcrypt hash signature."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False
