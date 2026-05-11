from datetime import date

from pydantic import BaseModel, ConfigDict


class FamilyTreeCreate(BaseModel):
    tree_name: str
    surname: str
    description: str | None = None


class FamilyTreeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tree_id: int
    tree_name: str
    surname: str
    compiled_at: date | None = None
    description: str | None = None


class AccessibleFamilyTreeResponse(FamilyTreeResponse):
    access_role: str
