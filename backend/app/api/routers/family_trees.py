from fastapi import APIRouter, Body, Depends, Query

from app.api.deps.auth import get_current_active_user
from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_creator, require_tree_editor, require_tree_reader
from app.models.user_account import UserAccount
from app.schemas.family_tree import (
    FamilyTreeCreateRequest,
    FamilyTreeDetailResponse,
    FamilyTreeResponse,
    FamilyTreeUpdateRequest,
    PaginatedFamilyTreeResponse,
)
from app.schemas.common import MessageResponse
from app.services.family_tree_service import FamilyTreeService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _family_tree_service(session: AsyncSession) -> FamilyTreeService:
    return FamilyTreeService(session)


@router.get("/", response_model=PaginatedFamilyTreeResponse)
async def list_family_trees(
    current_user: UserAccount = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedFamilyTreeResponse:
    return await _family_tree_service(session).list_accessible_for_user(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=FamilyTreeResponse)
async def create_family_tree(
    payload: FamilyTreeCreateRequest,
    current_user: UserAccount = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> FamilyTreeResponse:
    return await _family_tree_service(session).create(
        user_id=current_user.user_id,
        payload=payload,
    )


@router.get("/accessible", response_model=PaginatedFamilyTreeResponse)
async def accessible_family_trees(
    current_user: UserAccount = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedFamilyTreeResponse:
    return await _family_tree_service(session).list_accessible_for_user(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{tree_id}", response_model=FamilyTreeDetailResponse)
async def get_family_tree(
    tree_id: int,
    permission: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> FamilyTreeDetailResponse:
    return await _family_tree_service(session).get_detail(
        tree_id=tree_id,
        access_role=permission.role,
    )


@router.patch("/{tree_id}", response_model=FamilyTreeDetailResponse)
async def update_family_tree(
    tree_id: int,
    payload: FamilyTreeUpdateRequest | None = Body(default=None),
    permission: TreePermissionContext = Depends(require_tree_editor),
    session: AsyncSession = Depends(get_db_session),
) -> FamilyTreeDetailResponse:
    return await _family_tree_service(session).update(
        tree_id=tree_id,
        access_role=permission.role,
        payload=payload,
    )


@router.delete("/{tree_id}", response_model=MessageResponse)
async def delete_family_tree(
    tree_id: int,
    permission: TreePermissionContext = Depends(require_tree_creator),
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    await _family_tree_service(session).delete(tree_id=tree_id)
    return MessageResponse(message=f"Family tree {tree_id} deleted")
