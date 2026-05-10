from pydantic import BaseModel


class CollaboratorInviteRequest(BaseModel):
    user_id: int
    access_role: str

