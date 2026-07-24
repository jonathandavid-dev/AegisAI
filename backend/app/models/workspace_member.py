from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class WorkspaceMember(Base):
    """
    WorkspaceMember model tracking accounts enrolled in workspaces.
    """
    __tablename__ = "workspace_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="VIEWER", nullable=False) # OWNER, ADMIN, EDITOR, VIEWER
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    account = relationship("Account")
