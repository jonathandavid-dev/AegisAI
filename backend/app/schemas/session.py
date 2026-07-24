from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SessionResponse(BaseModel):
    """Placeholder schema for agent session responses."""
    id: int
    token: str
    account_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
