from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

FamilyTreeAccessRole = Literal["creator", "collaborator", "reader"]


class FamilyTreeCreateRequest(BaseModel):
    tree_name: str
    surname: str
    compiled_at: date | None = None
    description: str | None = None


class FamilyTreeUpdateRequest(BaseModel):
    tree_name: str | None = None
    surname: str | None = None
    compiled_at: date | None = None
    description: str | None = None


class FamilyTreeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tree_id: int
    tree_name: str
    surname: str
    compiled_at: date | None = None
    description: str | None = None


class FamilyTreeDetailResponse(FamilyTreeResponse):
    access_role: FamilyTreeAccessRole


class AccessibleFamilyTreeListItem(FamilyTreeResponse):
    access_role: FamilyTreeAccessRole


class PaginatedFamilyTreeResponse(BaseModel):
    items: list[AccessibleFamilyTreeListItem]
    total: int
    page: int
    page_size: int
