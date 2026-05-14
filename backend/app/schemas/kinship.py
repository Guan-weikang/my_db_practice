from pydantic import BaseModel

from app.schemas.search import MemberGraphNode


class AncestorNode(MemberGraphNode):
    depth: int
    child_member_id: int
    parent_role: str
    path_member_ids: list[int]


class AncestorResponse(BaseModel):
    start_member: MemberGraphNode
    max_depth: int
    nodes: list[AncestorNode]


class KinshipPathEdge(BaseModel):
    from_member_id: int
    to_member_id: int
    relation_type: str
    parent_role: str | None = None
    marriage_status: str | None = None


class KinshipPathResponse(BaseModel):
    exists: bool
    hop_count: int | None = None
    nodes: list[MemberGraphNode]
    edges: list[KinshipPathEdge]
