from pydantic import BaseModel, EmailStr, Field

class AuthRegisterRequest(BaseModel):
    """Pydantic model representing registration payloads."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = Field(None, max_length=100)
    role: str = Field("VIEWER", description="User role assignment (VIEWER, EDITOR, ADMIN)")

class AuthLoginRequest(BaseModel):
    """Pydantic model representing login payloads."""
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(...)

class ProfileUpdateRequest(BaseModel):
    """Pydantic model representing profile update payloads."""
    full_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = Field(None)
    password: str | None = Field(None, min_length=8)

class UserResponse(BaseModel):
    """Pydantic model representing serialized user account details."""
    id: int
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    """Pydantic model representing standard JWT token response payload."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
