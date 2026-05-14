from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_members: int
    male_count: int
    female_count: int
    unknown_count: int
    male_ratio: float | None = None
    female_ratio: float | None = None


class DashboardResponse(BaseModel):
    tree_id: int
    summary: DashboardSummary


class GenerationMaxAverageLifespanItem(BaseModel):
    generation_no: int
    avg_lifespan_years: float


class GenerationMaxAverageLifespanResponse(BaseModel):
    tree_id: int
    item: GenerationMaxAverageLifespanItem | None = None


class OlderThan50UnmarriedMaleItem(BaseModel):
    member_id: int
    name: str
    birth_date: date
    age_years: int
    generation_no: int | None = None
    generation_name: str | None = None


class OlderThan50UnmarriedMaleResponse(BaseModel):
    tree_id: int
    items: list[OlderThan50UnmarriedMaleItem]


class BeforeGenerationAverageBirthYearItem(BaseModel):
    member_id: int
    name: str
    generation_no: int
    generation_name: str | None = None
    birth_year: int
    avg_birth_year: float


class BeforeGenerationAverageBirthYearResponse(BaseModel):
    tree_id: int
    items: list[BeforeGenerationAverageBirthYearItem]
