from datetime import date

from pydantic import BaseModel


class MemberGraphNode(BaseModel):
    member_id: int
    tree_id: int
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    is_alive: bool
    generation_no: int | None = None
    generation_name: str | None = None


class SearchMemberItem(BaseModel):
    member_id: int
    tree_id: int
    name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    is_alive: bool
    generation_no: int | None = None
    generation_name: str | None = None
    father_name: str | None = None
    mother_name: str | None = None


class PaginatedSearchMemberResponse(BaseModel):
    items: list[SearchMemberItem]
    total: int
    page: int
    page_size: int


class BranchTreeNode(MemberGraphNode):
    depth: int
    parent_member_id: int | None = None
    incoming_parent_role: str | None = None
    path_member_ids: list[int]


class BranchTreeResponse(BaseModel):
    root_member: MemberGraphNode
    max_depth: int
    nodes: list[BranchTreeNode]
