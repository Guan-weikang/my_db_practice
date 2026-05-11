from datetime import datetime
from typing import Literal

from pydantic import BaseModel

CollaboratorAccessRole = Literal["collaborator", "reader"]
CollaboratorStatus = Literal["active", "revoked", "pending"]


class CollaboratorCreateRequest(BaseModel):
    user_id: int
    access_role: CollaboratorAccessRole


class CollaboratorUpdateRequest(BaseModel):
    access_role: CollaboratorAccessRole


class CollaboratorResponse(BaseModel):
    user_id: int
    username: str
    display_name: str | None = None
    access_role: CollaboratorAccessRole
    status: CollaboratorStatus
    invited_by: int
    invited_at: datetime


class PaginatedCollaboratorResponse(BaseModel):
    items: list[CollaboratorResponse]
    total: int
    page: int
    page_size: int
