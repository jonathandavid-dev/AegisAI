from app.models.workspace import Workspace
from app.models.organization import Organization

class TenantContext:
    """
    Encapsulates the current active workspace, organization,
    and the user's role inside this specific workspace context.
    """
    def __init__(self, workspace: Workspace, organization: Organization, member_role: str):
        self.workspace = workspace
        self.organization = organization
        self.member_role = member_role # OWNER, ADMIN, EDITOR, VIEWER
