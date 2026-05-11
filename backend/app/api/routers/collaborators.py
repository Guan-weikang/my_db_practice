from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.api.deps.permission import TreePermissionContext, require_tree_creator
from app.schemas.collaborator import (
    CollaboratorCreateRequest,
    CollaboratorResponse,
    CollaboratorUpdateRequest,
    PaginatedCollaboratorResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/", response_model=PaginatedCollaboratorResponse)
async def list_collaborators(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_creator),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedCollaboratorResponse:
    return PaginatedCollaboratorResponse(items=[], total=0, page=page, page_size=page_size)


@router.post("/", response_model=CollaboratorResponse)
async def invite_collaborator(
    tree_id: int,
    payload: CollaboratorCreateRequest,
    permission: TreePermissionContext = Depends(require_tree_creator),
) -> CollaboratorResponse:
    return CollaboratorResponse(
        user_id=payload.user_id,
        username="",
        display_name=None,
        access_role=payload.access_role,
        status="active",
        invited_by=permission.user.user_id,
        invited_at=datetime.now(timezone.utc),
    )


@router.patch("/{user_id}", response_model=CollaboratorResponse)
async def update_collaborator(
    tree_id: int,
    user_id: int,
    payload: CollaboratorUpdateRequest,
    permission: TreePermissionContext = Depends(require_tree_creator),
) -> CollaboratorResponse:
    return CollaboratorResponse(
        user_id=user_id,
        username="",
        display_name=None,
        access_role=payload.access_role,
        status="active",
        invited_by=permission.user.user_id,
        invited_at=datetime.now(timezone.utc),
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_collaborator(
    tree_id: int,
    user_id: int,
    _: TreePermissionContext = Depends(require_tree_creator),
) -> MessageResponse:
    return MessageResponse(message=f"remove collaborator {user_id} from tree {tree_id}")
