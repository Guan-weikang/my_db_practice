from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request
from app.queries.search_queries import MEMBER_SEARCH_QUERY
from app.schemas.search import PaginatedSearchMemberResponse, SearchMemberItem


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_members(
        self,
        *,
        tree_id: int,
        keyword: str,
        page: int,
        page_size: int,
    ) -> PaginatedSearchMemberResponse:
        normalized_keyword = self._normalize_keyword(keyword)
        self._validate_page(page)
        self._validate_page_size(page_size)

        offset = (page - 1) * page_size
        result = await self.session.execute(
            text(MEMBER_SEARCH_QUERY),
            {
                "tree_id": tree_id,
                "keyword": normalized_keyword,
                "keyword_prefix": f"{normalized_keyword}%",
                "offset": offset,
                "limit": page_size,
            },
        )
        rows = [dict(row._mapping) for row in result.all()]
        total = int(rows[0]["total_count"]) if rows else 0

        items = [
            SearchMemberItem(
                member_id=int(row["member_id"]),
                tree_id=int(row["tree_id"]),
                name=str(row["name"]),
                gender=str(row["gender"]),
                birth_date=row["birth_date"],
                death_date=row["death_date"],
                is_alive=bool(row["is_alive"]),
                generation_no=row["generation_no"],
                generation_name=row["generation_name"],
                father_name=row["father_name"],
                mother_name=row["mother_name"],
            )
            for row in rows
        ]
        return PaginatedSearchMemberResponse(items=items, total=total, page=page, page_size=page_size)

    @staticmethod
    def _normalize_keyword(keyword: str) -> str:
        normalized = keyword.strip()
        if len(normalized) < 2:
            raise bad_request("Search keyword must be at least 2 characters long")
        if len(normalized) > 50:
            raise bad_request("Search keyword must be at most 50 characters long")
        return normalized

    @staticmethod
    def _validate_page(page: int) -> None:
        if page < 1:
            raise bad_request("Search page must be a positive integer")

    @staticmethod
    def _validate_page_size(page_size: int) -> None:
        if page_size < 1 or page_size > 50:
            raise bad_request("Search page_size must be between 1 and 50")
