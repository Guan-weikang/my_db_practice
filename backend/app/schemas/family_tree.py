from pydantic import BaseModel


class FamilyTreeCreate(BaseModel):
    tree_name: str
    surname: str
    description: str | None = None


class FamilyTreeResponse(BaseModel):
    tree_id: int
    tree_name: str
    surname: str
    description: str | None = None

