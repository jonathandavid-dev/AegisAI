from datetime import datetime
from pydantic import BaseModel, EmailStr

class WorkspaceBase(BaseModel):
    name: str
    description: str | None = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceResponse(WorkspaceBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkspaceMemberResponse(BaseModel):
    account_id: int
    username: str
    email: str
    full_name: str | None = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

class MemberRoleUpdate(BaseModel):
    role: str

class WorkspaceInviteCreate(BaseModel):
    email: EmailStr

class WorkspaceInviteResponse(BaseModel):
    id: int
    workspace_id: int
    email: str
    invited_by: int
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
