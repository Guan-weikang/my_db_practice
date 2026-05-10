from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: int
    username: str
    display_name: str
    email: str | None
    status: str
    created_at: datetime | None = None

