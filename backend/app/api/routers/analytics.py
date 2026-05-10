from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def dashboard(tree_id: int) -> dict:
    return {"tree_id": tree_id, "total_members": 0, "male_count": 0, "female_count": 0}


@router.get("/generation/max-average-lifespan")
async def max_average_lifespan(tree_id: int) -> dict:
    return {"tree_id": tree_id, "generation_no": None, "avg_lifespan": None}


@router.get("/members/older-than-50-unmarried-male")
async def older_than_50_unmarried_male(tree_id: int) -> dict:
    return {"tree_id": tree_id, "items": []}


@router.get("/members/before-generation-average-birth-year")
async def before_generation_average_birth_year(tree_id: int) -> dict:
    return {"tree_id": tree_id, "items": []}

