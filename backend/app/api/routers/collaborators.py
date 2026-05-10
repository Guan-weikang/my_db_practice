from fastapi import APIRouter

from app.schemas.collaborator import CollaboratorInviteRequest

router = APIRouter()


@router.get("/")
async def list_collaborators(tree_id: int) -> dict:
    return {"tree_id": tree_id, "items": []}


@router.post("/")
async def invite_collaborator(tree_id: int, payload: CollaboratorInviteRequest) -> dict:
    return {"message": f"invite user {payload.user_id} to tree {tree_id}"}


@router.patch("/{user_id}")
async def update_collaborator(tree_id: int, user_id: int) -> dict:
    return {"message": f"update collaborator {user_id} in tree {tree_id}"}


@router.delete("/{user_id}")
async def delete_collaborator(tree_id: int, user_id: int) -> dict:
    return {"message": f"remove collaborator {user_id} from tree {tree_id}"}

