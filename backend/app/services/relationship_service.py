from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, conflict, not_found
from app.repositories.member_repository import MemberRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.relationship import (
    ChildRelationItem,
    MarriageCreateRequest,
    MarriageDeleteRequest,
    MarriageResponse,
    MarriageUpdateRequest,
    ParentChildCreateRequest,
    ParentChildDeleteRequest,
    ParentChildResponse,
    ParentRelationItem,
    SpouseRelationItem,
)


class RelationshipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.member_repository = MemberRepository(session)
        self.relationship_repository = RelationshipRepository(session)

    async def create_parent_child(self, *, tree_id: int, payload: ParentChildCreateRequest) -> ParentChildResponse:
        parent = await self._get_member_or_raise(tree_id=tree_id, member_id=payload.parent_member_id)
        child = await self._get_member_or_raise(tree_id=tree_id, member_id=payload.child_member_id)
        self._validate_parent_child_members(parent_member_id=parent.member_id, child_member_id=child.member_id)
        self._validate_parent_role_gender(parent_role=payload.parent_role, parent_gender=parent.gender)
        self._validate_parent_birth_order(parent_birth_date=parent.birth_date, child_birth_date=child.birth_date)

        existing_same_role = await self.relationship_repository.get_parent_by_child_and_role(
            tree_id=tree_id,
            child_member_id=payload.child_member_id,
            parent_role=payload.parent_role,
        )
        if existing_same_role is not None:
            if existing_same_role.parent_member_id == payload.parent_member_id:
                raise conflict("Parent-child relation already exists")
            raise conflict(f"Child already has a {payload.parent_role} in this family tree")

        if await self.relationship_repository.would_create_cycle(
            tree_id=tree_id,
            parent_member_id=payload.parent_member_id,
            child_member_id=payload.child_member_id,
        ):
            raise conflict("Parent-child relation would create an ancestor cycle")

        try:
            relation = await self.relationship_repository.create_parent_child(
                tree_id=tree_id,
                parent_member_id=payload.parent_member_id,
                child_member_id=payload.child_member_id,
                parent_role=payload.parent_role,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise conflict("Parent-child relation could not be created") from exc

        return ParentChildResponse(
            tree_id=relation.tree_id,
            parent_member_id=relation.parent_member_id,
            child_member_id=relation.child_member_id,
            parent_role=relation.parent_role,
        )

    async def delete_parent_child(self, *, tree_id: int, payload: ParentChildDeleteRequest) -> None:
        relation = await self.relationship_repository.get_parent_child(
            tree_id=tree_id,
            parent_member_id=payload.parent_member_id,
            child_member_id=payload.child_member_id,
            parent_role=payload.parent_role,
        )
        if relation is None:
            raise not_found("Parent-child relation not found")
        await self.relationship_repository.delete_parent_child(relation)
        await self.session.commit()

    async def list_parents(self, *, tree_id: int, member_id: int) -> list[ParentRelationItem]:
        await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        items = await self.relationship_repository.list_parents_for_member(tree_id=tree_id, member_id=member_id)
        return [ParentRelationItem(**item) for item in items]

    async def list_children(self, *, tree_id: int, member_id: int) -> list[ChildRelationItem]:
        await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        items = await self.relationship_repository.list_children_for_member(tree_id=tree_id, member_id=member_id)
        return [ChildRelationItem(**item) for item in items]

    async def create_marriage(self, *, tree_id: int, payload: MarriageCreateRequest) -> MarriageResponse:
        member_id_1, member_id_2 = self._normalize_marriage_members(payload.member_id_1, payload.member_id_2)
        member_1 = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id_1)
        member_2 = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id_2)
        self._validate_marriage_gender(member_1_gender=member_1.gender, member_2_gender=member_2.gender)
        self._validate_marriage_dates(married_at=payload.married_at, ended_at=payload.ended_at, status=payload.status)

        existing = await self.relationship_repository.get_marriage(
            tree_id=tree_id,
            member_id_1=member_id_1,
            member_id_2=member_id_2,
        )
        if existing is not None:
            raise conflict("Marriage relation already exists")
        if payload.status == "active":
            await self._ensure_no_other_active_marriage(tree_id=tree_id, member_id_1=member_id_1, member_id_2=member_id_2)

        try:
            marriage = await self.relationship_repository.create_marriage(
                tree_id=tree_id,
                member_id_1=member_id_1,
                member_id_2=member_id_2,
                married_at=payload.married_at,
                ended_at=payload.ended_at,
                status=payload.status,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise conflict("Marriage relation could not be created") from exc

        return MarriageResponse.model_validate(marriage)

    async def update_marriage(self, *, tree_id: int, payload: MarriageUpdateRequest) -> MarriageResponse:
        member_id_1, member_id_2 = self._normalize_marriage_members(payload.member_id_1, payload.member_id_2)
        marriage = await self.relationship_repository.get_marriage(
            tree_id=tree_id,
            member_id_1=member_id_1,
            member_id_2=member_id_2,
        )
        if marriage is None:
            raise not_found("Marriage relation not found")

        member_1 = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id_1)
        member_2 = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id_2)
        self._validate_marriage_gender(member_1_gender=member_1.gender, member_2_gender=member_2.gender)

        married_at = payload.married_at if "married_at" in payload.model_fields_set else marriage.married_at
        ended_at = payload.ended_at if "ended_at" in payload.model_fields_set else marriage.ended_at
        status = payload.status if payload.status is not None else marriage.status
        self._validate_marriage_dates(married_at=married_at, ended_at=ended_at, status=status)
        if status == "active":
            await self._ensure_no_other_active_marriage(
                tree_id=tree_id,
                member_id_1=member_id_1,
                member_id_2=member_id_2,
                exclude_pair=(member_id_1, member_id_2),
            )

        try:
            marriage = await self.relationship_repository.update_marriage(
                marriage,
                married_at=married_at,
                ended_at=ended_at,
                status=status,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise conflict("Marriage relation could not be updated") from exc

        return MarriageResponse.model_validate(marriage)

    async def delete_marriage(self, *, tree_id: int, payload: MarriageDeleteRequest) -> None:
        member_id_1, member_id_2 = self._normalize_marriage_members(payload.member_id_1, payload.member_id_2)
        marriage = await self.relationship_repository.get_marriage(
            tree_id=tree_id,
            member_id_1=member_id_1,
            member_id_2=member_id_2,
        )
        if marriage is None:
            raise not_found("Marriage relation not found")
        await self.relationship_repository.delete_marriage(marriage)
        await self.session.commit()

    async def list_spouses(self, *, tree_id: int, member_id: int) -> list[SpouseRelationItem]:
        await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        items = await self.relationship_repository.list_spouses_for_member(tree_id=tree_id, member_id=member_id)
        return [SpouseRelationItem(**item) for item in items]

    async def _get_member_or_raise(self, *, tree_id: int, member_id: int):
        member = await self.member_repository.get_by_tree_and_member_id(tree_id=tree_id, member_id=member_id)
        if member is None:
            raise not_found("Member not found")
        return member

    @staticmethod
    def _validate_parent_child_members(*, parent_member_id: int, child_member_id: int) -> None:
        if parent_member_id == child_member_id:
            raise conflict("Parent member and child member cannot be identical")

    @staticmethod
    def _validate_parent_birth_order(*, parent_birth_date, child_birth_date) -> None:
        if parent_birth_date is not None and child_birth_date is not None and parent_birth_date >= child_birth_date:
            raise bad_request("Parent birth_date must be earlier than child birth_date")

    @staticmethod
    def _validate_parent_role_gender(*, parent_role: str, parent_gender: str) -> None:
        if parent_role == "father" and parent_gender != "male":
            raise bad_request("Father relation requires parent gender to be male")
        if parent_role == "mother" and parent_gender != "female":
            raise bad_request("Mother relation requires parent gender to be female")

    @staticmethod
    def _normalize_marriage_members(member_id_1: int, member_id_2: int) -> tuple[int, int]:
        if member_id_1 == member_id_2:
            raise conflict("Marriage members cannot be identical")
        return (member_id_1, member_id_2) if member_id_1 < member_id_2 else (member_id_2, member_id_1)

    @staticmethod
    def _validate_marriage_gender(*, member_1_gender: str, member_2_gender: str) -> None:
        valid_genders = {member_1_gender, member_2_gender}
        if "unknown" in valid_genders:
            raise bad_request("Marriage relation requires both members to have known gender")
        if member_1_gender == member_2_gender:
            raise bad_request("Marriage relation requires one male member and one female member")

    async def _ensure_no_other_active_marriage(
        self,
        *,
        tree_id: int,
        member_id_1: int,
        member_id_2: int,
        exclude_pair: tuple[int, int] | None = None,
    ) -> None:
        active_marriage_for_member_1 = await self.relationship_repository.find_active_marriage_for_member(
            tree_id=tree_id,
            member_id=member_id_1,
            exclude_pair=exclude_pair,
        )
        if active_marriage_for_member_1 is not None:
            raise conflict("Member already has another active marriage")

        active_marriage_for_member_2 = await self.relationship_repository.find_active_marriage_for_member(
            tree_id=tree_id,
            member_id=member_id_2,
            exclude_pair=exclude_pair,
        )
        if active_marriage_for_member_2 is not None:
            raise conflict("Member already has another active marriage")

    @staticmethod
    def _validate_marriage_dates(*, married_at, ended_at, status: str) -> None:
        if married_at is not None and ended_at is not None and ended_at < married_at:
            raise bad_request("Marriage ended_at cannot be earlier than married_at")
        if status == "active" and ended_at is not None:
            raise bad_request("Active marriage cannot have ended_at")
        if status == "ended" and ended_at is None:
            raise bad_request("Ended marriage must provide ended_at")
