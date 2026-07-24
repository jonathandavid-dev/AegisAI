from typing import List

class ExecutionContext:
    """Encapsulates caller credentials, workspace context, and permission scopes for secure tool execution."""
    
    def __init__(self, account_id: int, workspace_id: int = 1, permissions: List[str] = None):
        self.account_id = account_id
        self.workspace_id = workspace_id
        self.permissions = permissions or ["read"]
