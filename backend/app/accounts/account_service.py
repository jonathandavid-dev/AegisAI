import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.account import Account
from app.auth.password_service import PasswordService

logger = structlog.get_logger("aegis.accounts")

class AccountService:
    """Handles updating account profiles, changing emails, and modifying passwords."""
    
    @staticmethod
    async def update_profile(
        db: AsyncSession,
        account_id: int,
        full_name: str | None = None,
        email: str | None = None,
        password: str | None = None
    ) -> Account:
        """Applies name changes, verifies email uniqueness, and updates password hashes."""
        stmt = select(Account).where(Account.id == account_id)
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        
        if not account:
            logger.warn("Account update target missing", account_id=account_id)
            raise ValueError("Account not found.")
            
        if full_name is not None:
            account.full_name = full_name
            
        if email is not None and email != account.email:
            # Check unique constraint on email
            stmt_uniq = select(Account).where(Account.email == email)
            res_uniq = await db.execute(stmt_uniq)
            if res_uniq.scalars().first():
                raise ValueError("An account with this email already exists.")
            account.email = email
            
        if password is not None:
            if not PasswordService.is_complex(password):
                raise ValueError("Password must contain at least 8 characters, one number, one uppercase, and one special character.")
            account.hashed_password = PasswordService.hash_password(password)
            
        await db.commit()
        await db.refresh(account)
        logger.info("Profile updated", username=account.username)
        return account
