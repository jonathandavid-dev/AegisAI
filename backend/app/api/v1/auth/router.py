from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.auth.auth_service import AuthService
from app.accounts.account_service import AccountService
from app.audit.audit_service import AuditService
from app.schemas.auth import AuthRegisterRequest, AuthLoginRequest, ProfileUpdateRequest, AuthResponse, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: AuthRegisterRequest, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new user and logs a REGISTER audit event."""
    try:
        account = await AuthService.register_user(
            db=db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role
        )
        
        await AuditService.log_event(
            db=db,
            account_id=account.id,
            action="REGISTER",
            resource="account",
            resource_id=str(account.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata_json={"username": account.username, "email": account.email}
        )
        
        return account
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.post("/login", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: AuthLoginRequest, 
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verifies user credentials, sets refresh token cookies, and registers a LOGIN audit event."""
    try:
        account, access_token, refresh_token = await AuthService.login_user(
            db=db,
            username_or_email=payload.username_or_email,
            password=payload.password
        )
        
        # Configuresecure HttpOnly cookie for refresh token storage
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        
        await AuditService.log_event(
            db=db,
            account_id=account.id,
            action="LOGIN",
            resource="account",
            resource_id=str(account.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "access_token": access_token,
            "user": account
        }
    except (ValueError, PermissionError) as exc:
        status_code = status.HTTP_403_FORBIDDEN if isinstance(exc, PermissionError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc))

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """Revokes the refresh token, clears auth cookies, and registers a LOGOUT audit event."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await AuthService.logout_user(db, refresh_token)
        
    response.delete_cookie("refresh_token")
    
    await AuditService.log_event(
        db=db,
        account_id=current_account.id,
        action="LOGOUT",
        resource="account",
        resource_id=str(current_account.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/refresh", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Validates and rotates refresh tokens, returning a refreshed access token."""
    refresh_token = request.cookies.get("refresh_token")
    
    # Fallback to Authorization Header if cookies are blocked
    if not refresh_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]
            
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")
        
    try:
        access_token, new_refresh = await AuthService.refresh_tokens(db, refresh_token)
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        
        # Decode subject claims to resolve the Account object
        from app.auth.jwt_service import JWTService
        payload = JWTService.decode_access_token(access_token)
        user_id = int(payload.get("sub"))
        
        from sqlalchemy import select
        res = await db.execute(select(Account).where(Account.id == user_id))
        account = res.scalar_one()
        
        await AuditService.log_event(
            db=db,
            account_id=account.id,
            action="TOKEN_REFRESH",
            resource="token",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "access_token": access_token,
            "user": account
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def me(current_account: Account = Depends(get_current_account)):
    """Returns the authenticated account profile data."""
    return current_account

@router.patch("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """Updates profile credentials and logs a PROFILE_UPDATE audit event."""
    try:
        updated = await AccountService.update_profile(
            db=db,
            account_id=current_account.id,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password
        )
        
        await AuditService.log_event(
            db=db,
            account_id=current_account.id,
            action="PROFILE_UPDATE",
            resource="account",
            resource_id=str(current_account.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
