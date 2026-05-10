from pydantic import BaseModel


class ParentChildCreate(BaseModel):
    parent_member_id: int
    child_member_id: int
    parent_role: str


class MarriageCreate(BaseModel):
    member_id_1: int
    member_id_2: int

