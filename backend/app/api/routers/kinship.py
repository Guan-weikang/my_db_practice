from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_reader
from app.schemas.kinship import AncestorResponse, KinshipPathResponse
from app.services.kinship_service import KinshipService

router = APIRouter()


def _kinship_service(session: AsyncSession) -> KinshipService:
    return KinshipService(session)


@router.get("/ancestors/{member_id}", response_model=AncestorResponse)
async def ancestors(
    tree_id: int,
    member_id: int,
    max_depth: int = Query(30, ge=1, le=100),
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> AncestorResponse:
    return await _kinship_service(session).get_ancestors(
        tree_id=tree_id,
        member_id=member_id,
        max_depth=max_depth,
    )


@router.get("/path", response_model=KinshipPathResponse)
async def path(
    tree_id: int,
    member_a: int,
    member_b: int,
    max_depth: int = Query(12, ge=1, le=20),
    include_ended_marriages: bool = Query(False),
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> KinshipPathResponse:
    return await _kinship_service(session).get_path(
        tree_id=tree_id,
        member_a=member_a,
        member_b=member_b,
        max_depth=max_depth,
        include_ended_marriages=include_ended_marriages,
    )
