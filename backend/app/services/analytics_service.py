from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.queries.analytics_queries import DASHBOARD_QUERY
from app.schemas.analytics import (
    BeforeGenerationAverageBirthYearResponse,
    DashboardResponse,
    DashboardSummary,
    GenerationMaxAverageLifespanResponse,
    OlderThan50UnmarriedMaleResponse,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_dashboard(self, *, tree_id: int) -> DashboardResponse:
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
        return GenerationMaxAverageLifespanResponse(tree_id=tree_id, item=None)

    async def get_older_than_50_unmarried_male(self, *, tree_id: int) -> OlderThan50UnmarriedMaleResponse:
        return OlderThan50UnmarriedMaleResponse(tree_id=tree_id, items=[])

    async def get_before_generation_average_birth_year(
        self,
        *,
        tree_id: int,
    ) -> BeforeGenerationAverageBirthYearResponse:
        return BeforeGenerationAverageBirthYearResponse(tree_id=tree_id, items=[])
