from fastapi import APIRouter

from app.schemas.family_tree import FamilyTreeCreate

router = APIRouter()


@router.get("/")
async def list_family_trees() -> dict:
    return {"items": []}


@router.post("/")
async def create_family_tree(payload: FamilyTreeCreate) -> dict:
    return {"message": f"create family tree {payload.tree_name}"}


@router.get("/accessible")
async def accessible_family_trees() -> dict:
    return {"items": []}


@router.get("/{tree_id}")
async def get_family_tree(tree_id: int) -> dict:
    return {"tree_id": tree_id}


@router.patch("/{tree_id}")
async def update_family_tree(tree_id: int) -> dict:
    return {"message": f"update family tree {tree_id}"}


@router.delete("/{tree_id}")
async def delete_family_tree(tree_id: int) -> dict:
    return {"message": f"delete family tree {tree_id}"}

