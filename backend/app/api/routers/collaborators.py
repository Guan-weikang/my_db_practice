from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import get_response_cache
from app.api.deps.permission import TreePermissionContext, require_tree_creator
from app.api.deps.db import get_db_session
from app.core.cache import ResponseCache
from app.schemas.collaborator import (
    CollaboratorCreateRequest,
    CollaboratorResponse,
    CollaboratorUpdateRequest,
    PaginatedCollaboratorResponse,
)
from app.schemas.common import MessageResponse
from app.services.collaborator_service import CollaboratorService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _collaborator_service(session: AsyncSession, cache: ResponseCache | None = None) -> CollaboratorService:
    return CollaboratorService(session, cache)


@router.get("/", response_model=PaginatedCollaboratorResponse)
async def list_collaborators(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_creator),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedCollaboratorResponse:
    return await _collaborator_service(session).list_for_tree(tree_id=tree_id, page=page, page_size=page_size)


@router.post("/", response_model=CollaboratorResponse)
async def invite_collaborator(
    tree_id: int,
    payload: CollaboratorCreateRequest,
    permission: TreePermissionContext = Depends(require_tree_creator),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> CollaboratorResponse:
    return await _collaborator_service(session, cache).create(
        tree_id=tree_id,
        invited_by=permission.user_id,
        payload=payload,
    )


@router.patch("/{user_id}", response_model=CollaboratorResponse)
async def update_collaborator(
    tree_id: int,
    user_id: int,
    payload: CollaboratorUpdateRequest,
    _: TreePermissionContext = Depends(require_tree_creator),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> CollaboratorResponse:
    return await _collaborator_service(session, cache).update(
        tree_id=tree_id,
        user_id=user_id,
        payload=payload,
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_collaborator(
    tree_id: int,
    user_id: int,
    _: TreePermissionContext = Depends(require_tree_creator),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> MessageResponse:
    await _collaborator_service(session, cache).revoke(tree_id=tree_id, user_id=user_id)
    return MessageResponse(message=f"Collaborator {user_id} revoked from family tree {tree_id}")
