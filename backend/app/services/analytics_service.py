from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import ResponseCache
from app.queries.analytics_queries import (
    BEFORE_GENERATION_AVERAGE_BIRTH_YEAR_QUERY,
    DASHBOARD_QUERY,
    MAX_AVERAGE_LIFESPAN_QUERY,
    OLDER_THAN_50_UNMARRIED_MALE_QUERY,
)
from app.schemas.analytics import (
    BeforeGenerationAverageBirthYearItem,
    BeforeGenerationAverageBirthYearResponse,
    DashboardResponse,
    DashboardSummary,
    GenerationMaxAverageLifespanItem,
    GenerationMaxAverageLifespanResponse,
    OlderThan50UnmarriedMaleItem,
    OlderThan50UnmarriedMaleResponse,
)
from app.services.cache_helpers import get_or_set_model


class AnalyticsService:
    def __init__(self, session: AsyncSession, cache: ResponseCache | None = None) -> None:
        self.session = session
        self.cache = cache

    async def get_dashboard(self, *, tree_id: int) -> DashboardResponse:
        return await get_or_set_model(
            self.cache,
            key=f"tree:{tree_id}:analytics:dashboard",
            ttl_seconds=300,
            model_type=DashboardResponse,
            loader=lambda: self._get_dashboard_uncached(tree_id=tree_id),
        )

    async def _get_dashboard_uncached(self, *, tree_id: int) -> DashboardResponse:
        result = await self.session.execute(text(DASHBOARD_QUERY), {"tree_id": tree_id})
        row = dict(result.one()._mapping)
        return DashboardResponse(
            tree_id=int(row["tree_id"]),
            summary=DashboardSummary(
                total_members=int(row["total_members"]),
                male_count=int(row["male_count"]),
                female_count=int(row["female_count"]),
                unknown_count=int(row["unknown_count"]),
                male_ratio=float(row["male_ratio"]) if row["male_ratio"] is not None else None,
                female_ratio=float(row["female_ratio"]) if row["female_ratio"] is not None else None,
            ),
        )

    async def get_max_average_lifespan(self, *, tree_id: int) -> GenerationMaxAverageLifespanResponse:
        return await get_or_set_model(
            self.cache,
            key=f"tree:{tree_id}:analytics:max-average-lifespan",
            ttl_seconds=300,
            model_type=GenerationMaxAverageLifespanResponse,
            loader=lambda: self._get_max_average_lifespan_uncached(tree_id=tree_id),
        )

    async def _get_max_average_lifespan_uncached(self, *, tree_id: int) -> GenerationMaxAverageLifespanResponse:
        result = await self.session.execute(text(MAX_AVERAGE_LIFESPAN_QUERY), {"tree_id": tree_id})
        row = result.first()
        if row is None:
            return GenerationMaxAverageLifespanResponse(tree_id=tree_id, item=None)

        payload = dict(row._mapping)
        return GenerationMaxAverageLifespanResponse(
            tree_id=int(payload["tree_id"]),
            item=GenerationMaxAverageLifespanItem(
                generation_no=int(payload["generation_no"]),
                avg_lifespan_years=float(payload["avg_lifespan_years"]),
            ),
        )

    async def get_older_than_50_unmarried_male(self, *, tree_id: int) -> OlderThan50UnmarriedMaleResponse:
        return await get_or_set_model(
            self.cache,
            key=f"tree:{tree_id}:analytics:older-than-50-unmarried-male",
            ttl_seconds=300,
            model_type=OlderThan50UnmarriedMaleResponse,
            loader=lambda: self._get_older_than_50_unmarried_male_uncached(tree_id=tree_id),
        )

    async def _get_older_than_50_unmarried_male_uncached(self, *, tree_id: int) -> OlderThan50UnmarriedMaleResponse:
        result = await self.session.execute(text(OLDER_THAN_50_UNMARRIED_MALE_QUERY), {"tree_id": tree_id})
        rows = [dict(row._mapping) for row in result.all()]
        return OlderThan50UnmarriedMaleResponse(
            tree_id=tree_id,
            items=[
                OlderThan50UnmarriedMaleItem(
                    member_id=int(row["member_id"]),
                    name=str(row["name"]),
                    birth_date=row["birth_date"],
                    age_years=int(row["age_years"]),
                    generation_no=row["generation_no"],
                    generation_name=row["generation_name"],
                )
                for row in rows
            ],
        )

    async def get_before_generation_average_birth_year(
        self,
        *,
        tree_id: int,
    ) -> BeforeGenerationAverageBirthYearResponse:
        return await get_or_set_model(
            self.cache,
            key=f"tree:{tree_id}:analytics:before-generation-average-birth-year",
            ttl_seconds=300,
            model_type=BeforeGenerationAverageBirthYearResponse,
            loader=lambda: self._get_before_generation_average_birth_year_uncached(tree_id=tree_id),
        )

    async def _get_before_generation_average_birth_year_uncached(
        self,
        *,
        tree_id: int,
    ) -> BeforeGenerationAverageBirthYearResponse:
        result = await self.session.execute(text(BEFORE_GENERATION_AVERAGE_BIRTH_YEAR_QUERY), {"tree_id": tree_id})
        rows = [dict(row._mapping) for row in result.all()]
        return BeforeGenerationAverageBirthYearResponse(
            tree_id=tree_id,
            items=[
                BeforeGenerationAverageBirthYearItem(
                    member_id=int(row["member_id"]),
                    name=str(row["name"]),
                    generation_no=int(row["generation_no"]),
                    generation_name=row["generation_name"],
                    birth_year=int(row["birth_year"]),
                    avg_birth_year=float(row["avg_birth_year"]),
                )
                for row in rows
            ],
        )
