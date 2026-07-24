import enum

class UserRole(str, enum.Enum):
    """System-wide role designations."""
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"
