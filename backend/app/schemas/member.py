from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MemberCreateRequest(BaseModel):
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    is_alive: bool = True
    generation_no: int | None = None
    generation_name: str | None = None
    biography: str | None = None


class MemberUpdateRequest(BaseModel):
    name: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    is_alive: bool | None = None
    generation_no: int | None = None
    generation_name: str | None = None
    biography: str | None = None


class MemberListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    tree_id: int
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    is_alive: bool
    generation_no: int | None = None
    generation_name: str | None = None


class MemberDetailResponse(MemberListItem):
    biography: str | None = None
    created_at: datetime
    updated_at: datetime


class PaginatedMemberResponse(BaseModel):
    items: list[MemberListItem]
    total: int
    page: int
    page_size: int


class MemberIdRangeResponse(BaseModel):
    min_member_id: int | None = None
    max_member_id: int | None = None
    total: int
