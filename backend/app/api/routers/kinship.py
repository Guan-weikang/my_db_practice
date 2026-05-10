from fastapi import APIRouter

router = APIRouter()


@router.get("/ancestors/{member_id}")
async def ancestors(tree_id: int, member_id: int) -> dict:
    return {"tree_id": tree_id, "member_id": member_id, "ancestors": []}


@router.get("/path")
async def path(tree_id: int, member_a: int, member_b: int) -> dict:
    return {"tree_id": tree_id, "member_a": member_a, "member_b": member_b, "path": []}

