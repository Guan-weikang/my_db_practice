from datetime import date

from pydantic import BaseModel


class MemberCreate(BaseModel):
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    generation_no: int | None = None
    generation_name: str | None = None
    biography: str | None = None


class MemberResponse(BaseModel):
    member_id: int
    tree_id: int
    name: str
    gender: str
    generation_no: int | None = None
    generation_name: str | None = None

