import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken
from app.config.settings import settings

class TokenService:
    """Computes SHA-256 hashes, generates token chains, and revokes refresh tokens."""
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Computes a secure SHA-256 hash of a raw token string."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    async def create_refresh_token(cls, db: AsyncSession, account_id: int) -> str:
        """Generates a cryptographically secure random token, hashes, and persists it."""
        raw_token = secrets.token_urlsafe(64)
        token_hash = cls._hash_token(raw_token)
        
        days = getattr(settings, "JWT_REFRESH_TOKEN_DAYS", 7)
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        
        db_token = RefreshToken(
            account_id=account_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_token)
        await db.commit()
        return raw_token

    @classmethod
    async def rotate_refresh_token(cls, db: AsyncSession, raw_token: str) -> str | None:
        """Revokes the old token and issues a new, rotated refresh token."""
        token_hash = cls._hash_token(raw_token)
        
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False
        )
        res = await db.execute(stmt)
        db_token = res.scalar_one_or_none()
        
        if not db_token:
            return None
            
        # Verify lifetime
        exp_time = db_token.expires_at.replace(tzinfo=timezone.utc)
        if exp_time < datetime.now(timezone.utc):
            return None
            
        # Revoke old token
        db_token.revoked = True
        await db.commit()
        
        # Issue new rotated token
        return await cls.create_refresh_token(db, db_token.account_id)

    @classmethod
    async def revoke_refresh_token(cls, db: AsyncSession, raw_token: str) -> bool:
        """Invalidates a refresh token by marking it as revoked."""
        token_hash = cls._hash_token(raw_token)
        
        stmt = update(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        ).values(revoked=True)
        
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @classmethod
    async def get_account_id_from_refresh_token(cls, db: AsyncSession, raw_token: str) -> int | None:
        """Extracts the owning account ID for a valid token, checking expiration."""
        token_hash = cls._hash_token(raw_token)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False
        )
        res = await db.execute(stmt)
        db_token = res.scalar_one_or_none()
        
        if not db_token:
            return None
            
        exp_time = db_token.expires_at.replace(tzinfo=timezone.utc)
        if exp_time < datetime.now(timezone.utc):
            return None
            
        return db_token.account_id
