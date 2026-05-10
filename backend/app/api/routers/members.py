from fastapi import APIRouter

from app.schemas.member import MemberCreate

router = APIRouter()


@router.get("/")
async def list_members(tree_id: int) -> dict:
    return {"tree_id": tree_id, "items": []}


@router.post("/")
async def create_member(tree_id: int, payload: MemberCreate) -> dict:
    return {"message": f"create member {payload.name} in tree {tree_id}"}


@router.get("/{member_id}")
async def get_member(tree_id: int, member_id: int) -> dict:
    return {"tree_id": tree_id, "member_id": member_id}


@router.patch("/{member_id}")
async def update_member(tree_id: int, member_id: int) -> dict:
    return {"message": f"update member {member_id} in tree {tree_id}"}


@router.delete("/{member_id}")
async def delete_member(tree_id: int, member_id: int) -> dict:
    return {"message": f"delete member {member_id} in tree {tree_id}"}

