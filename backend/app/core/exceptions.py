from typing import Any, Optional

class AegisException(Exception):
    """Base exception for AegisAI application."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

class ApplicationException(AegisException):
    """General purpose application error."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)

class AuthenticationException(AegisException):
    """Exception raised for invalid authentication or authorization."""
    def __init__(self, message: str = "Authentication credentials invalid", details: Optional[Any] = None):
        super().__init__(message, status_code=401, details=details)

class DatabaseException(AegisException):
    """Database query or connection failure."""
    def __init__(self, message: str = "A database operations failure occurred", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)

class ValidationException(AegisException):
    """Input payload validation failure."""
    def __init__(self, message: str = "Request input validation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=422, details=details)
