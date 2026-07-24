from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.conversation import MessageRole

class MessageResponse(BaseModel):
    """Schema representing an individual message inside a conversation history."""
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    """Schema representing metadata and status fields for a conversation session."""
    id: int
    account_id: int
    title: str
    summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationTitleUpdate(BaseModel):
    """Schema validating patch updates for conversation session titles."""
    title: str = Field(..., min_length=1, max_length=255, description="New title for the session.")
