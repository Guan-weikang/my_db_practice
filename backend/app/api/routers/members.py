from fastapi import APIRouter, Body, Depends, Query, status

from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_editor, require_tree_reader
from app.schemas.common import MessageResponse
from app.schemas.member import (
    MemberCreateRequest,
    MemberDetailResponse,
    MemberUpdateRequest,
    PaginatedMemberResponse,
)
from app.services.member_service import MemberService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _member_service(session: AsyncSession) -> MemberService:
    return MemberService(session)


@router.get("", response_model=PaginatedMemberResponse)
async def list_members(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedMemberResponse:
    return await _member_service(session).list_by_tree(tree_id=tree_id, page=page, page_size=page_size)


@router.post("", response_model=MemberDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    tree_id: int,
    payload: MemberCreateRequest,
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
) -> MemberDetailResponse:
    return await _member_service(session).create(tree_id=tree_id, payload=payload)


@router.get("/{member_id}", response_model=MemberDetailResponse)
async def get_member(
    tree_id: int,
    member_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> MemberDetailResponse:
    return await _member_service(session).get_detail(tree_id=tree_id, member_id=member_id)


@router.patch("/{member_id}", response_model=MemberDetailResponse)
async def update_member(
    tree_id: int,
    member_id: int,
    payload: MemberUpdateRequest | None = Body(default=None),
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
) -> MemberDetailResponse:
    return await _member_service(session).update(tree_id=tree_id, member_id=member_id, payload=payload)


@router.delete("/{member_id}", response_model=MessageResponse)
async def delete_member(
    tree_id: int,
    member_id: int,
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    await _member_service(session).delete(tree_id=tree_id, member_id=member_id)
    return MessageResponse(message=f"Member {member_id} deleted from family tree {tree_id}")
