from fastapi import APIRouter, Body, Depends

from app.api.deps.auth import get_response_cache
from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_editor, require_tree_reader
from app.core.cache import ResponseCache
from app.schemas.common import MessageResponse
from app.schemas.relationship import (
    ChildRelationItem,
    MarriageCreateRequest,
    MarriageDeleteRequest,
    MarriageResponse,
    MarriageUpdateRequest,
    ParentChildCreateRequest,
    ParentChildDeleteRequest,
    ParentChildResponse,
    ParentRelationItem,
    SpouseRelationItem,
)
from app.services.relationship_service import RelationshipService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _relationship_service(session: AsyncSession, cache: ResponseCache | None = None) -> RelationshipService:
    return RelationshipService(session, cache)


@router.post("/parent-child")
async def create_parent_child(
    tree_id: int,
    payload: ParentChildCreateRequest,
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> ParentChildResponse:
    return await _relationship_service(session, cache).create_parent_child(tree_id=tree_id, payload=payload)


@router.delete("/parent-child", response_model=MessageResponse)
async def delete_parent_child(
    tree_id: int,
    payload: ParentChildDeleteRequest = Body(...),
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> MessageResponse:
    await _relationship_service(session, cache).delete_parent_child(tree_id=tree_id, payload=payload)
    return MessageResponse(message="Parent-child relation deleted")


@router.post("/marriages")
async def create_marriage(
    tree_id: int,
    payload: MarriageCreateRequest,
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> MarriageResponse:
    return await _relationship_service(session, cache).create_marriage(tree_id=tree_id, payload=payload)


@router.patch("/marriages")
async def update_marriage(
    tree_id: int,
    payload: MarriageUpdateRequest,
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> MarriageResponse:
    return await _relationship_service(session, cache).update_marriage(tree_id=tree_id, payload=payload)


@router.delete("/marriages", response_model=MessageResponse)
async def delete_marriage(
    tree_id: int,
    payload: MarriageDeleteRequest = Body(...),
    _: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> MessageResponse:
    await _relationship_service(session, cache).delete_marriage(tree_id=tree_id, payload=payload)
    return MessageResponse(message="Marriage relation deleted")


@router.get("/members/{member_id}/parents")
async def member_parents(
    tree_id: int,
    member_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> list[ParentRelationItem]:
    return await _relationship_service(session).list_parents(tree_id=tree_id, member_id=member_id)


@router.get("/members/{member_id}/children")
async def member_children(
    tree_id: int,
    member_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> list[ChildRelationItem]:
    return await _relationship_service(session).list_children(tree_id=tree_id, member_id=member_id)


@router.get("/members/{member_id}/spouses")
async def member_spouses(
    tree_id: int,
    member_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> list[SpouseRelationItem]:
    return await _relationship_service(session).list_spouses(tree_id=tree_id, member_id=member_id)
