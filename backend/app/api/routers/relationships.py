from fastapi import APIRouter

from app.schemas.relationship import MarriageCreate, ParentChildCreate

router = APIRouter()


@router.post("/parent-child")
async def create_parent_child(tree_id: int, payload: ParentChildCreate) -> dict:
    return {"message": f"create parent-child relation in tree {tree_id}", "payload": payload.model_dump()}


@router.delete("/parent-child")
async def delete_parent_child(tree_id: int) -> dict:
    return {"message": f"delete parent-child relation in tree {tree_id}"}


@router.post("/marriages")
async def create_marriage(tree_id: int, payload: MarriageCreate) -> dict:
    return {"message": f"create marriage in tree {tree_id}", "payload": payload.model_dump()}


@router.delete("/marriages")
async def delete_marriage(tree_id: int) -> dict:
    return {"message": f"delete marriage in tree {tree_id}"}


@router.get("/members/{member_id}/parents")
async def member_parents(tree_id: int, member_id: int) -> dict:
    return {"tree_id": tree_id, "member_id": member_id, "parents": []}


@router.get("/members/{member_id}/children")
async def member_children(tree_id: int, member_id: int) -> dict:
    return {"tree_id": tree_id, "member_id": member_id, "children": []}


@router.get("/members/{member_id}/spouses")
async def member_spouses(tree_id: int, member_id: int) -> dict:
    return {"tree_id": tree_id, "member_id": member_id, "spouses": []}

