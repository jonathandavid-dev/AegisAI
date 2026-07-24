from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class AccountBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid corporate email address")

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=8, max_length=100, description="Secure user password")

class AccountResponse(AccountBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str = Field(..., description="Registered username")
    password: str = Field(..., description="Registered password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
