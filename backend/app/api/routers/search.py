from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/members")
async def search_members(tree_id: int, keyword: str = Query(...)) -> dict:
    return {"tree_id": tree_id, "keyword": keyword, "items": []}


@router.get("/branch-tree")
async def branch_tree(tree_id: int, root_member_id: int) -> dict:
    return {"tree_id": tree_id, "root_member_id": root_member_id, "items": []}

