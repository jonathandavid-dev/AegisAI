import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.config.settings import settings

class JWTService:
    """Encodes and decodes signed JWT access tokens with strict expiration validation."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Generates a signed JWT access token containing subject claims."""
        to_encode = data.copy()
        
        # Fallback to configured settings minutes
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            minutes = getattr(settings, "JWT_ACCESS_TOKEN_MINUTES", 15)
            expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            
        to_encode.update({"exp": int(expire.timestamp())})
        
        secret = getattr(settings, "JWT_SECRET", settings.SECRET_KEY)
        return jwt.encode(to_encode, secret, algorithm="HS256")

    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any] | None:
        """Validates the signature and expiration payload of a token string."""
        try:
            secret = getattr(settings, "JWT_SECRET", settings.SECRET_KEY)
            return jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.PyJWTError:
            return None
