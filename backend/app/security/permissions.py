import structlog
from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.security.roles import UserRole

logger = structlog.get_logger("aegis.security")

# Mapping permission strings to authorized role scopes
PERMISSION_ROLES = {
    "document:upload": [UserRole.ADMIN, UserRole.EDITOR],
    "document:delete": [UserRole.ADMIN],
    "chat:read_write": [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER],
    "admin:ops": [UserRole.ADMIN],
}

class PermissionChecker:
    """Enforces specific action permission checks against user role scopes using FastAPI dependency gates."""
    
    def __init__(self, permission: str):
        self.permission = permission
        
    def __call__(self, current_user: Account = Depends(get_current_account)) -> Account:
        allowed_roles = PERMISSION_ROLES.get(self.permission, [])
        role_val = getattr(current_user, "role", None)
        user_role = (role_val or "ADMIN").upper()
        
        allowed_values = [r.value for r in allowed_roles]
        if user_role not in allowed_values:
            logger.warn(
                "Permission Denied", 
                username=current_user.username, 
                role=current_user.role, 
                required_permission=self.permission
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission Denied: Insufficient user credentials scope."
            )
        return current_user
