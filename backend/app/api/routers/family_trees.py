from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_active_user
from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_creator, require_tree_editor, require_tree_reader
from app.models.user_account import UserAccount
from app.repositories.family_tree_repository import FamilyTreeRepository
from app.schemas.family_tree import AccessibleFamilyTreeResponse, FamilyTreeCreate, FamilyTreeResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/")
async def list_family_trees(
    current_user: UserAccount = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    items = await FamilyTreeRepository(session).list_accessible_for_user(current_user.user_id)
    return {"items": [AccessibleFamilyTreeResponse(**item).model_dump() for item in items]}


@router.post("/")
async def create_family_tree(
    payload: FamilyTreeCreate,
    current_user: UserAccount = Depends(get_current_active_user),
) -> dict:
    return {"message": f"create family tree {payload.tree_name}", "creator_user_id": current_user.user_id}


@router.get("/accessible")
async def accessible_family_trees(
    current_user: UserAccount = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    items = await FamilyTreeRepository(session).list_accessible_for_user(current_user.user_id)
    return {"items": [AccessibleFamilyTreeResponse(**item).model_dump() for item in items]}


@router.get("/{tree_id}", response_model=FamilyTreeResponse)
async def get_family_tree(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> FamilyTreeResponse:
    tree = await FamilyTreeRepository(session).get_by_id(tree_id)
    return FamilyTreeResponse.model_validate(tree)


@router.patch("/{tree_id}")
async def update_family_tree(
    tree_id: int,
    permission: TreePermissionContext = Depends(require_tree_editor),
) -> dict:
    return {"message": f"update family tree {tree_id}", "role": permission.role}


@router.delete("/{tree_id}")
async def delete_family_tree(
    tree_id: int,
    permission: TreePermissionContext = Depends(require_tree_creator),
) -> dict:
    return {"message": f"delete family tree {tree_id}", "role": permission.role}
