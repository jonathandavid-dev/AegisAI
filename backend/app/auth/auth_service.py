import time
import structlog
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.account import Account
from app.auth.password_service import PasswordService
from app.auth.jwt_service import JWTService
from app.auth.token_service import TokenService
from app.config.settings import settings

logger = structlog.get_logger("aegis.auth")

# In-memory dictionary tracking failed login attempts
# key: string (username/email), value: tuple (attempts_count, lock_until_datetime)
FAILED_ATTEMPTS: dict[str, tuple[int, datetime | None]] = {}

class AuthService:
    """Manages secure registration, locked credentials tracking, and token lifecycles."""
    
    @staticmethod
    async def register_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
        role: str = "VIEWER"
    ) -> Account:
        """Validates complexity, check uniqueness constraints, and hashes the new account."""
        # 1. Enforce password complexity check
        if not PasswordService.is_complex(password):
            logger.warn("password_complexity_failed", username=username)
            raise ValueError("Password must contain at least 8 characters, one number, one uppercase, and one special character.")
            
        # 2. Check for username/email conflicts
        stmt = select(Account).where(
            (Account.username == username) | (Account.email == email)
        )
        res = await db.execute(stmt)
        if res.scalars().first():
            logger.warn("registration_conflict", username=username, email=email)
            raise ValueError("An account with this username or email already exists.")
            
        # 3. Hash password and persist account details
        hashed = PasswordService.hash_password(password)
        account = Account(
            username=username,
            email=email,
            hashed_password=hashed,
            full_name=full_name,
            role=role.upper(),
            is_active=True,
            is_verified=False
        )
        
        db.add(account)
        await db.commit()
        await db.refresh(account)
        
        # Auto-provision default organization and workspace for the user
        from app.organizations.organization_service import OrganizationService
        await OrganizationService.create_organization(
            db=db,
            name=f"{username}'s Organization",
            owner_id=account.id
        )
        
        logger.info("Registration", status="success", username=username, role=account.role)
        return account

    @staticmethod
    async def login_user(
        db: AsyncSession,
        username_or_email: str,
        password: str
    ) -> tuple[Account, str, str]:
        """Verifies credentials, checks lock status, rotates refresh/access token, and tracks failures."""
        now = datetime.now(timezone.utc)
        
        attempts, lock_until = FAILED_ATTEMPTS.get(username_or_email, (0, None))
        max_attempts = getattr(settings, "MAX_LOGIN_ATTEMPTS", 5)
        lock_mins = getattr(settings, "ACCOUNT_LOCK_DURATION", 15)
        
        if lock_until and lock_until > now:
            diff = int((lock_until - now).total_seconds())
            logger.warn("account_locked", username_or_email=username_or_email, seconds_left=diff)
            raise PermissionError(f"Account is temporarily locked. Try again in {diff} seconds.")
            
        # 2. Query account record
        stmt = select(Account).where(
            (Account.username == username_or_email) | (Account.email == username_or_email)
        )
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        
        if not account or not account.is_active:
            logger.warn("Failed login", identifier=username_or_email, reason="not_found_or_inactive")
            new_attempts = attempts + 1
            new_lock = now + timedelta(minutes=lock_mins) if new_attempts >= max_attempts else None
            FAILED_ATTEMPTS[username_or_email] = (new_attempts, new_lock)
            raise ValueError("Invalid username or password.")
            
        # 3. Match hash credentials
        if not PasswordService.verify_password(password, account.hashed_password):
            logger.warn("Failed login", username=account.username, attempts=attempts + 1)
            new_attempts = attempts + 1
            new_lock = now + timedelta(minutes=lock_mins) if new_attempts >= max_attempts else None
            FAILED_ATTEMPTS[username_or_email] = (new_attempts, new_lock)
            raise ValueError("Invalid username or password.")
            
        # Reset failed attempts counters
        FAILED_ATTEMPTS[username_or_email] = (0, None)
        
        # Update last login timestamp
        account.last_login = now
        await db.commit()
        
        # Issue tokens
        access_token = JWTService.create_access_token({
            "sub": str(account.id),
            "username": account.username,
            "role": account.role
        })
        refresh_token = await TokenService.create_refresh_token(db, account.id)
        
        logger.info("Authentication", status="success", username=account.username)
        return account, access_token, refresh_token

    @staticmethod
    async def refresh_tokens(db: AsyncSession, raw_refresh_token: str) -> tuple[str, str]:
        """Validates refresh token and returns a new access token pair."""
        account_id = await TokenService.get_account_id_from_refresh_token(db, raw_refresh_token)
        if not account_id:
            logger.warn("Token refresh failed", reason="invalid_token")
            raise PermissionError("Invalid or expired refresh token.")
            
        stmt = select(Account).where(Account.id == account_id)
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        
        if not account or not account.is_active:
            raise PermissionError("Account is inactive.")
            
        # Rotate refresh token
        new_refresh = await TokenService.rotate_refresh_token(db, raw_refresh_token)
        if not new_refresh:
            raise PermissionError("Failed to rotate refresh token.")
            
        # Generate access token
        access_token = JWTService.create_access_token({
            "sub": str(account.id),
            "username": account.username,
            "role": account.role
        })
        
        logger.info("Token refresh", status="success", username=account.username)
        return access_token, new_refresh

    @staticmethod
    async def logout_user(db: AsyncSession, raw_refresh_token: str) -> None:
        """Revokes token chains to safely end active user sessions."""
        revoked = await TokenService.revoke_refresh_token(db, raw_refresh_token)
        if revoked:
            logger.info("Token Revoked", trigger="logout")
