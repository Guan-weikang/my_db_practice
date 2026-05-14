from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, not_found
from app.repositories.member_repository import MemberRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.member import (
    MemberCreateRequest,
    MemberDetailResponse,
    MemberIdRangeResponse,
    MemberListItem,
    MemberUpdateRequest,
    PaginatedMemberResponse,
)


class MemberService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.member_repository = MemberRepository(session)
        self.relationship_repository = RelationshipRepository(session)

    async def list_by_tree(self, *, tree_id: int, page: int, page_size: int) -> PaginatedMemberResponse:
        offset = (page - 1) * page_size
        items = await self.member_repository.list_by_tree_id(tree_id, offset=offset, limit=page_size)
        total = await self.member_repository.count_by_tree_id(tree_id)
        return PaginatedMemberResponse(
            items=[MemberListItem.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_id_range(self, *, tree_id: int) -> MemberIdRangeResponse:
        min_member_id, max_member_id, total = await self.member_repository.get_member_id_range_by_tree_id(tree_id)
        return MemberIdRangeResponse(
            min_member_id=min_member_id,
            max_member_id=max_member_id,
            total=total,
        )

    async def get_detail(self, *, tree_id: int, member_id: int) -> MemberDetailResponse:
        member = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        return MemberDetailResponse.model_validate(member)

    async def create(self, *, tree_id: int, payload: MemberCreateRequest) -> MemberDetailResponse:
        values = self._build_create_values(payload)
        member = await self.member_repository.create(tree_id=tree_id, values=values)
        await self.session.commit()
        await self.session.refresh(member)
        return MemberDetailResponse.model_validate(member)

    async def update(self, *, tree_id: int, member_id: int, payload: MemberUpdateRequest | None) -> MemberDetailResponse:
        member = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        values = self._build_update_values(member=member, payload=payload)
        if values:
            member = await self.member_repository.update(member, values)
            await self.session.commit()
            await self.session.refresh(member)
        return MemberDetailResponse.model_validate(member)

    async def delete(self, *, tree_id: int, member_id: int) -> None:
        member = await self._get_member_or_raise(tree_id=tree_id, member_id=member_id)
        await self.relationship_repository.delete_relations_for_member(tree_id=tree_id, member_id=member.member_id)
        await self.member_repository.delete(member)
        await self.session.commit()

    async def _get_member_or_raise(self, *, tree_id: int, member_id: int):
        member = await self.member_repository.get_by_tree_and_member_id(tree_id=tree_id, member_id=member_id)
        if member is None:
            raise not_found("Member not found")
        return member

    def _build_create_values(self, payload: MemberCreateRequest) -> dict[str, object | None]:
        normalized_name = self._normalize_required_name(payload.name)
        self._validate_dates(birth_date=payload.birth_date, death_date=payload.death_date, is_alive=payload.is_alive)
        self._validate_generation_no(payload.generation_no)
        self._validate_gender(payload.gender)
        return {
            "name": normalized_name,
            "gender": payload.gender,
            "birth_date": payload.birth_date,
            "death_date": payload.death_date,
            "is_alive": payload.is_alive,
            "generation_no": payload.generation_no,
            "generation_name": self._normalize_optional_text(payload.generation_name),
            "biography": self._normalize_optional_text(payload.biography),
        }

    def _build_update_values(self, *, member, payload: MemberUpdateRequest | None) -> dict[str, object | None]:
        values: dict[str, object | None] = {}
        if payload is None:
            return values

        if "name" in payload.model_fields_set:
            if payload.name is None:
                raise bad_request("Member name cannot be null")
            values["name"] = self._normalize_required_name(payload.name)

        if "gender" in payload.model_fields_set:
            if payload.gender is None:
                raise bad_request("Member gender cannot be null")
            self._validate_gender(payload.gender)
            values["gender"] = payload.gender

        if "birth_date" in payload.model_fields_set:
            values["birth_date"] = payload.birth_date

        if "death_date" in payload.model_fields_set:
            values["death_date"] = payload.death_date

        if "is_alive" in payload.model_fields_set:
            if payload.is_alive is None:
                raise bad_request("Member is_alive cannot be null")
            values["is_alive"] = payload.is_alive

        if "generation_no" in payload.model_fields_set:
            self._validate_generation_no(payload.generation_no)
            values["generation_no"] = payload.generation_no

        if "generation_name" in payload.model_fields_set:
            values["generation_name"] = self._normalize_optional_text(payload.generation_name)

        if "biography" in payload.model_fields_set:
            values["biography"] = self._normalize_optional_text(payload.biography)

        birth_date = values["birth_date"] if "birth_date" in values else member.birth_date
        death_date = values["death_date"] if "death_date" in values else member.death_date
        is_alive = values["is_alive"] if "is_alive" in values else member.is_alive
        self._validate_dates(birth_date=birth_date, death_date=death_date, is_alive=is_alive)
        return values

    @staticmethod
    def _normalize_required_name(value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise bad_request("Member name cannot be empty")
        return normalized

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _validate_gender(value: str) -> None:
        if value not in {"male", "female", "unknown"}:
            raise bad_request("Member gender must be one of: male, female, unknown")

    @staticmethod
    def _validate_generation_no(value: int | None) -> None:
        if value is not None and value <= 0:
            raise bad_request("Member generation_no must be a positive integer")

    @staticmethod
    def _validate_dates(*, birth_date, death_date, is_alive: bool) -> None:
        if birth_date is not None and death_date is not None and death_date < birth_date:
            raise bad_request("Member death_date cannot be earlier than birth_date")
        if is_alive and death_date is not None:
            raise bad_request("Living member cannot have death_date")
