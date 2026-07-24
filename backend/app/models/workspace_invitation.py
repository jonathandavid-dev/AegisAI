from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class WorkspaceInvitation(Base):
    """
    WorkspaceInvitation model tracking membership invitations.
    """
    __tablename__ = "workspace_invitations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    invited_by: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False) # PENDING, ACCEPTED, DECLINED, EXPIRED
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    inviter = relationship("Account")
