from fastapi import APIRouter

from app.api.routers.analytics import router as analytics_router
from app.api.routers.auth import router as auth_router
from app.api.routers.collaborators import router as collaborators_router
from app.api.routers.family_trees import router as family_trees_router
from app.api.routers.health import router as health_router
from app.api.routers.kinship import router as kinship_router
from app.api.routers.members import router as members_router
from app.api.routers.relationships import router as relationships_router
from app.api.routers.search import router as search_router
from app.api.routers.users import router as users_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(family_trees_router, prefix="/family-trees", tags=["family-trees"])
router.include_router(collaborators_router, prefix="/family-trees/{tree_id}/collaborators", tags=["collaborators"])
router.include_router(members_router, prefix="/family-trees/{tree_id}/members", tags=["members"])
router.include_router(relationships_router, prefix="/family-trees/{tree_id}/relationships", tags=["relationships"])
router.include_router(search_router, prefix="/family-trees/{tree_id}/search", tags=["search"])
router.include_router(analytics_router, prefix="/family-trees/{tree_id}/analytics", tags=["analytics"])
router.include_router(kinship_router, prefix="/family-trees/{tree_id}/kinship", tags=["kinship"])

