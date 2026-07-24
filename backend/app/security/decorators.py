from functools import wraps
from typing import Callable, Any, List
from app.models.account import Account

def require_roles(allowed_roles: List[str]):
    """Python wrapper decorator to check user account role scopes in standard function calls."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = None
            for arg in args:
                if isinstance(arg, Account):
                    user = arg
                    break
            if not user:
                for k, v in kwargs.items():
                    if isinstance(v, Account):
                        user = v
                        break
            if not user or user.role.upper() not in [r.upper() for r in allowed_roles]:
                raise PermissionError("Access Denied: Account lacks required role credentials.")
            return func(*args, **kwargs)
        return wrapper
    return decorator
