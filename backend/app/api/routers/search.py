from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_reader
from app.schemas.search import BranchTreeResponse, PaginatedSearchMemberResponse
from app.services.search_service import SearchService

router = APIRouter()


def _search_service(session: AsyncSession) -> SearchService:
    return SearchService(session)


@router.get("/members", response_model=PaginatedSearchMemberResponse)
async def search_members(
    tree_id: int,
    keyword: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedSearchMemberResponse:
    return await _search_service(session).search_members(
        tree_id=tree_id,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

@router.get("/branch-tree", response_model=BranchTreeResponse)
async def branch_tree(
    tree_id: int,
    root_member_id: int,
    max_depth: int = Query(4, ge=1, le=10),
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
) -> BranchTreeResponse:
    return await _search_service(session).get_branch_tree(
        tree_id=tree_id,
        root_member_id=root_member_id,
        max_depth=max_depth,
    )
