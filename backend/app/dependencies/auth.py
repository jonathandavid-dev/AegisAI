from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.models.account import Account
from app.auth.jwt_service import JWTService

security = HTTPBearer(auto_error=True)

async def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Account:
    """
    Validates the bearer access token and returns the authenticated Account model.
    """
    from app.observability.tracing import trace_span
    from app.observability.logging import bind_observability_fields

    with trace_span("Authentication"):
        token = credentials.credentials
        payload = JWTService.decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token."
            )
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload."
            )
            
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identifier."
            )
            
        stmt = select(Account).where(Account.id == user_id)
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found."
            )
            
        if not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive."
            )
            
        bind_observability_fields(account_id=account.id)
        return account

