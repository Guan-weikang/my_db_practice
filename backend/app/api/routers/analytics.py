from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_response_cache
from app.api.deps.db import get_db_session
from app.api.deps.permission import TreePermissionContext, require_tree_reader
from app.core.cache import ResponseCache
from app.schemas.analytics import (
    BeforeGenerationAverageBirthYearResponse,
    DashboardResponse,
    GenerationMaxAverageLifespanResponse,
    OlderThan50UnmarriedMaleResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


def _analytics_service(session: AsyncSession, cache: ResponseCache | None) -> AnalyticsService:
    return AnalyticsService(session, cache)


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> DashboardResponse:
    return await _analytics_service(session, cache).get_dashboard(tree_id=tree_id)


@router.get("/generation/max-average-lifespan", response_model=GenerationMaxAverageLifespanResponse)
async def max_average_lifespan(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> GenerationMaxAverageLifespanResponse:
    return await _analytics_service(session, cache).get_max_average_lifespan(tree_id=tree_id)


@router.get("/members/older-than-50-unmarried-male", response_model=OlderThan50UnmarriedMaleResponse)
async def older_than_50_unmarried_male(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> OlderThan50UnmarriedMaleResponse:
    return await _analytics_service(session, cache).get_older_than_50_unmarried_male(tree_id=tree_id)


@router.get(
    "/members/before-generation-average-birth-year",
    response_model=BeforeGenerationAverageBirthYearResponse,
)
async def before_generation_average_birth_year(
    tree_id: int,
    _: TreePermissionContext = Depends(require_tree_reader),
    session: AsyncSession = Depends(get_db_session),
    cache: ResponseCache = Depends(get_response_cache),
) -> BeforeGenerationAverageBirthYearResponse:
    return await _analytics_service(session, cache).get_before_generation_average_birth_year(tree_id=tree_id)
