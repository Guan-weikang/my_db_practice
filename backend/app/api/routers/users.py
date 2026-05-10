from fastapi import APIRouter

router = APIRouter()


@router.get("/{user_id}")
async def get_user(user_id: int) -> dict:
    return {"user_id": user_id}


@router.patch("/me")
async def update_me() -> dict:
    return {"message": "update current user placeholder"}

