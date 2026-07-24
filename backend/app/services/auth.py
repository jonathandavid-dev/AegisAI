from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.account import Account
from app.schemas.account import AccountCreate, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import AuthenticationException, ApplicationException

class AuthService:
    """Service layer coordinating credential checks, registration, and JWT creation."""
    
    @staticmethod
    async def get_account_by_username(db: AsyncSession, username: str) -> Account | None:
        """Retrieves Account entity from DB by username."""
        result = await db.execute(select(Account).where(Account.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_account_by_email(db: AsyncSession, email: str) -> Account | None:
        """Retrieves Account entity from DB by email address."""
        result = await db.execute(select(Account).where(Account.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def register(db: AsyncSession, account_in: AccountCreate) -> Account:
        """Registers a new User Account with hashed password protection."""
        existing_username = await AuthService.get_account_by_username(db, account_in.username)
        if existing_username:
            raise ApplicationException(message="Username is already registered")
            
        existing_email = await AuthService.get_account_by_email(db, account_in.email)
        if existing_email:
            raise ApplicationException(message="Email is already registered")

        hashed = hash_password(account_in.password)
        db_account = Account(
            username=account_in.username,
            email=account_in.email,
            hashed_password=hashed,
            is_active=True
        )
        db.add(db_account)
        await db.commit()
        await db.refresh(db_account)
        return db_account

    @staticmethod
    async def authenticate(db: AsyncSession, login_in: LoginRequest) -> str:
        """Authenticates user credentials and generates access token."""
        account = await AuthService.get_account_by_username(db, login_in.username)
        if not account:
            raise AuthenticationException(message="Incorrect username or password")
            
        if not account.is_active:
            raise AuthenticationException(message="This account is currently deactivated")
            
        if not verify_password(login_in.password, account.hashed_password):
            raise AuthenticationException(message="Incorrect username or password")
            
        return create_access_token(subject=account.username)
