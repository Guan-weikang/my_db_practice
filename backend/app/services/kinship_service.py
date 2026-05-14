from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, not_found
from app.queries.ancestor_queries import ANCESTOR_QUERY
from app.queries.kinship_queries import (
    KINSHIP_PATH_EDGE_DETAILS_QUERY,
    KINSHIP_PATH_NODE_DETAILS_QUERY,
    KINSHIP_NEIGHBOR_QUERY,
)
from app.repositories.member_repository import MemberRepository
from app.schemas.kinship import AncestorNode, AncestorResponse, KinshipPathEdge, KinshipPathResponse
from app.schemas.search import MemberGraphNode


class KinshipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.member_repository = MemberRepository(session)

    async def get_ancestors(self, *, tree_id: int, member_id: int, max_depth: int) -> AncestorResponse:
        self._validate_ancestor_depth(max_depth)
        start_member = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        result = await self.session.execute(
            text(ANCESTOR_QUERY),
            {
                "tree_id": tree_id,
                "member_id": member_id,
                "max_depth": max_depth,
            },
        )
        rows = [dict(row._mapping) for row in result.all()]
        nodes = [
            AncestorNode(
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
                child_member_id=int(row["child_member_id"]),
                parent_role=str(row["parent_role"]),
                path_member_ids=[int(path_member_id) for path_member_id in row["path_member_ids"]],
            )
            for row in rows
        ]
        return AncestorResponse(
            start_member=self._to_member_graph_node(start_member),
            max_depth=max_depth,
            nodes=nodes,
        )

    async def get_path(
        self,
        *,
        tree_id: int,
        member_a: int,
        member_b: int,
        max_depth: int,
        include_ended_marriages: bool,
    ) -> KinshipPathResponse:
        self._validate_path_depth(max_depth)
        member_a_record = await self._get_member_or_raise(tree_id=tree_id, member_id=member_a)
        member_b_record = await self._get_member_or_raise(tree_id=tree_id, member_id=member_b)

        if member_a == member_b:
            return KinshipPathResponse(
                exists=True,
                hop_count=0,
                nodes=[self._to_member_graph_node(member_a_record)],
                edges=[],
            )

        path_member_ids = await self._find_path_member_ids(
            tree_id=tree_id,
            member_a=member_a,
            member_b=member_b,
            max_depth=max_depth,
            include_ended_marriages=include_ended_marriages,
        )
        if path_member_ids is None:
            return KinshipPathResponse(exists=False, hop_count=None, nodes=[], edges=[])

        node_rows = await self.session.execute(
            text(KINSHIP_PATH_NODE_DETAILS_QUERY),
            {
                "tree_id": tree_id,
                "path_member_ids": path_member_ids,
            },
        )
        nodes = [
            MemberGraphNode(
                member_id=int(row["member_id"]),
                tree_id=int(row["tree_id"]),
                name=str(row["name"]),
                gender=str(row["gender"]),
                birth_date=row["birth_date"],
                death_date=row["death_date"],
                is_alive=bool(row["is_alive"]),
                generation_no=row["generation_no"],
                generation_name=row["generation_name"],
            )
            for row in [dict(record._mapping) for record in node_rows.all()]
        ]
        edge_rows = await self.session.execute(
            text(KINSHIP_PATH_EDGE_DETAILS_QUERY),
            {
                "tree_id": tree_id,
                "path_member_ids": path_member_ids,
                "include_ended_marriages": include_ended_marriages,
            },
        )
        edges = [
            KinshipPathEdge(
                from_member_id=int(row["from_member_id"]),
                to_member_id=int(row["to_member_id"]),
                relation_type=str(row["relation_type"]),
                parent_role=row["parent_role"],
                marriage_status=row["marriage_status"],
            )
            for row in [dict(record._mapping) for record in edge_rows.all()]
        ]
        return KinshipPathResponse(
            exists=True,
            hop_count=len(path_member_ids) - 1,
            nodes=nodes,
            edges=edges,
        )

    async def _find_path_member_ids(
        self,
        *,
        tree_id: int,
        member_a: int,
        member_b: int,
        max_depth: int,
        include_ended_marriages: bool,
    ) -> list[int] | None:
        start_paths: dict[int, list[int]] = {member_a: [member_a]}
        target_paths: dict[int, list[int]] = {member_b: [member_b]}
        start_frontier = {member_a}
        target_frontier = {member_b}

        for _ in range(max_depth):
            expand_from_start = len(start_frontier) <= len(target_frontier)
            active_frontier = start_frontier if expand_from_start else target_frontier
            active_paths = start_paths if expand_from_start else target_paths
            other_paths = target_paths if expand_from_start else start_paths

            if not active_frontier:
                return None

            edges = await self._load_neighbor_edges(
                tree_id=tree_id,
                frontier_member_ids=active_frontier,
                include_ended_marriages=include_ended_marriages,
            )
            next_frontier: set[int] = set()

            for from_member, to_member in edges:
                if to_member in active_paths:
                    continue

                path = [*active_paths[from_member], to_member]
                if len(path) - 1 > max_depth:
                    continue

                active_paths[to_member] = path
                if to_member in other_paths:
                    if expand_from_start:
                        combined_path = path + list(reversed(other_paths[to_member]))[1:]
                    else:
                        combined_path = other_paths[to_member] + list(reversed(path))[1:]
                    if len(combined_path) - 1 <= max_depth:
                        return combined_path
                next_frontier.add(to_member)

            if expand_from_start:
                start_frontier = next_frontier
            else:
                target_frontier = next_frontier

        return None

    async def _load_neighbor_edges(
        self,
        *,
        tree_id: int,
        frontier_member_ids: set[int],
        include_ended_marriages: bool,
    ) -> list[tuple[int, int]]:
        result = await self.session.execute(
            text(KINSHIP_NEIGHBOR_QUERY),
            {
                "tree_id": tree_id,
                "frontier_member_ids": sorted(frontier_member_ids),
                "include_ended_marriages": include_ended_marriages,
            },
        )
        return [(int(row["from_member"]), int(row["to_member"])) for row in [dict(record._mapping) for record in result.all()]]

    @staticmethod
    def _validate_ancestor_depth(max_depth: int) -> None:
        if max_depth < 1 or max_depth > 100:
            raise bad_request("Ancestor max_depth must be between 1 and 100")

    @staticmethod
    def _validate_path_depth(max_depth: int) -> None:
        if max_depth < 1 or max_depth > 20:
            raise bad_request("Kinship path max_depth must be between 1 and 20")

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
