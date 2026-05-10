from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_members: int
    male_count: int
    female_count: int

