from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import ResponseCache
from app.core.exceptions import bad_request, not_found
from app.queries.search_queries import BRANCH_TREE_QUERY, MEMBER_SEARCH_QUERY
from app.repositories.member_repository import MemberRepository
from app.schemas.search import (
    BranchTreeNode,
    BranchTreeResponse,
    MemberGraphNode,
    PaginatedSearchMemberResponse,
    SearchMemberItem,
)
from app.services.cache_helpers import get_or_set_model


class SearchService:
    def __init__(self, session: AsyncSession, cache: ResponseCache | None = None) -> None:
        self.session = session
        self.cache = cache
        self.member_repository = MemberRepository(session)

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

    async def get_branch_tree(self, *, tree_id: int, root_member_id: int, max_depth: int) -> BranchTreeResponse:
        return await get_or_set_model(
            self.cache,
            key=f"tree:{tree_id}:branch-tree:root:{root_member_id}:depth:{max_depth}",
            ttl_seconds=300,
            model_type=BranchTreeResponse,
            loader=lambda: self._get_branch_tree_uncached(
                tree_id=tree_id,
                root_member_id=root_member_id,
                max_depth=max_depth,
            ),
        )

    async def _get_branch_tree_uncached(self, *, tree_id: int, root_member_id: int, max_depth: int) -> BranchTreeResponse:
        self._validate_branch_depth(max_depth)
        root_member = await self._get_member_or_raise(tree_id=tree_id, member_id=root_member_id)
        result = await self.session.execute(
            text(BRANCH_TREE_QUERY),
            {
                "tree_id": tree_id,
                "root_member_id": root_member_id,
                "max_depth": max_depth,
            },
        )
        rows = [dict(row._mapping) for row in result.all()]
        nodes = [
            BranchTreeNode(
                member_id=int(row["member_id"]),
                tree_id=int(row["tree_id"]),
                name=str(row["name"]),
                gender=str(row["gender"]),
                birth_date=row["birth_date"],
                death_date=row["death_date"],
                is_alive=bool(row["is_alive"]),
                generation_no=row["generation_no"],
                generation_name=row["generation_name"],
                depth=int(row["depth"]),
                parent_member_id=row["parent_member_id"],
                incoming_parent_role=row["incoming_parent_role"],
                path_member_ids=[int(member_id) for member_id in row["path_member_ids"]],
            )
            for row in rows
        ]
        return BranchTreeResponse(
            root_member=self._to_member_graph_node(root_member),
            max_depth=max_depth,
            nodes=nodes,
        )

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

    @staticmethod
    def _validate_branch_depth(max_depth: int) -> None:
        if max_depth < 1 or max_depth > 10:
            raise bad_request("Branch tree max_depth must be between 1 and 10")

    async def _get_member_or_raise(self, *, tree_id: int, member_id: int):
        member = await self.member_repository.get_by_tree_and_member_id(tree_id=tree_id, member_id=member_id)
        if member is None:
            raise not_found("Member not found")
        return member

    @staticmethod
    def _to_member_graph_node(member) -> MemberGraphNode:
        return MemberGraphNode(
            member_id=member.member_id,
            tree_id=member.tree_id,
            name=member.name,
            gender=member.gender,
            birth_date=member.birth_date,
            death_date=member.death_date,
            is_alive=member.is_alive,
            generation_no=member.generation_no,
            generation_name=member.generation_name,
        )
