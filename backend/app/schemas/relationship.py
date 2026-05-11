from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

ParentRole = Literal["father", "mother"]
MarriageStatus = Literal["active", "ended"]


class ParentChildCreateRequest(BaseModel):
    parent_member_id: int
    child_member_id: int
    parent_role: ParentRole


class ParentChildDeleteRequest(ParentChildCreateRequest):
    pass


class ParentChildResponse(BaseModel):
    tree_id: int
    parent_member_id: int
    child_member_id: int
    parent_role: ParentRole


class MarriageCreateRequest(BaseModel):
    member_id_1: int
    member_id_2: int
    married_at: date | None = None
    ended_at: date | None = None
    status: MarriageStatus = "active"


class MarriageUpdateRequest(BaseModel):
    member_id_1: int
    member_id_2: int
    married_at: date | None = None
    ended_at: date | None = None
    status: MarriageStatus | None = None


class MarriageDeleteRequest(BaseModel):
    member_id_1: int
    member_id_2: int


class MarriageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tree_id: int
    member_id_1: int
    member_id_2: int
    married_at: date | None = None
    ended_at: date | None = None
    status: MarriageStatus


class ParentRelationItem(BaseModel):
    parent_member_id: int
    parent_role: ParentRole
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    generation_no: int | None = None
    generation_name: str | None = None


class ChildRelationItem(BaseModel):
    child_member_id: int
    parent_role: ParentRole
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    generation_no: int | None = None
    generation_name: str | None = None


class SpouseRelationItem(BaseModel):
    spouse_member_id: int
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    generation_no: int | None = None
    generation_name: str | None = None
    married_at: date | None = None
    ended_at: date | None = None
    status: MarriageStatus
