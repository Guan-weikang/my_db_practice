from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, conflict, not_found
from app.repositories.collaborator_repository import CollaboratorRepository
from app.repositories.family_tree_repository import FamilyTreeRepository
from app.repositories.member_repository import MemberRepository
from app.schemas.family_tree import (
    AccessibleFamilyTreeListItem,
    FamilyTreeCreateRequest,
    FamilyTreeDetailResponse,
    FamilyTreeResponse,
    FamilyTreeUpdateRequest,
    PaginatedFamilyTreeResponse,
)


class FamilyTreeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.family_tree_repository = FamilyTreeRepository(session)
        self.collaborator_repository = CollaboratorRepository(session)
        self.member_repository = MemberRepository(session)

    async def list_accessible_for_user(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> PaginatedFamilyTreeResponse:
        offset = (page - 1) * page_size
        items = await self.family_tree_repository.list_accessible_for_user(
            user_id,
            offset=offset,
            limit=page_size,
        )
        total = await self.family_tree_repository.count_accessible_for_user(user_id)
        return PaginatedFamilyTreeResponse(
            items=[AccessibleFamilyTreeListItem(**item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_detail(self, *, tree_id: int, access_role: str) -> FamilyTreeDetailResponse:
        tree = await self.family_tree_repository.get_by_id(tree_id)
        if tree is None:
            raise not_found("Family tree not found")
        return FamilyTreeDetailResponse(
            **FamilyTreeResponse.model_validate(tree).model_dump(),
            access_role=access_role,
        )

    async def create(self, *, user_id: int, payload: FamilyTreeCreateRequest) -> FamilyTreeResponse:
        self._validate_create_payload(payload)
        tree = await self.family_tree_repository.create(
            tree_name=payload.tree_name.strip(),
            surname=payload.surname.strip(),
            creator_user_id=user_id,
            compiled_at=payload.compiled_at,
            description=self._normalize_optional_text(payload.description),
        )
        await self.session.commit()
        await self.session.refresh(tree)
        return FamilyTreeResponse.model_validate(tree)

    async def update(
        self,
        *,
        tree_id: int,
        access_role: str,
        payload: FamilyTreeUpdateRequest | None,
    ) -> FamilyTreeDetailResponse:
        tree = await self.family_tree_repository.get_by_id(tree_id)
        if tree is None:
            raise not_found("Family tree not found")

        update_values = self._build_update_values(payload)
        if not update_values:
            return FamilyTreeDetailResponse(
                **FamilyTreeResponse.model_validate(tree).model_dump(),
                access_role=access_role,
            )

        tree = await self.family_tree_repository.update(tree, update_values)
        await self.session.commit()
        await self.session.refresh(tree)
        return FamilyTreeDetailResponse(
            **FamilyTreeResponse.model_validate(tree).model_dump(),
            access_role=access_role,
        )

    async def delete(self, *, tree_id: int) -> None:
        tree = await self.family_tree_repository.get_by_id(tree_id)
        if tree is None:
            raise not_found("Family tree not found")
        member_count = await self.member_repository.count_by_tree_id(tree_id)
        if member_count > 0:
            raise conflict("Only empty family trees can be physically deleted at this stage")
        await self.collaborator_repository.delete_by_tree_id(tree_id)
        await self.family_tree_repository.delete(tree)
        await self.session.commit()

    def _validate_create_payload(self, payload: FamilyTreeCreateRequest) -> None:
        if not payload.tree_name.strip():
            raise bad_request("Family tree name cannot be empty")
        if not payload.surname.strip():
            raise bad_request("Family surname cannot be empty")

    def _build_update_values(self, payload: FamilyTreeUpdateRequest | None) -> dict[str, object | None]:
        values: dict[str, object | None] = {}
        if payload is None:
            return values

        if "tree_name" in payload.model_fields_set:
            if payload.tree_name is None or not payload.tree_name.strip():
                raise bad_request("Family tree name cannot be empty")
            values["tree_name"] = payload.tree_name.strip()

        if "surname" in payload.model_fields_set:
            if payload.surname is None or not payload.surname.strip():
                raise bad_request("Family surname cannot be empty")
            values["surname"] = payload.surname.strip()

        if "compiled_at" in payload.model_fields_set:
            values["compiled_at"] = payload.compiled_at

        if "description" in payload.model_fields_set:
            values["description"] = self._normalize_optional_text(payload.description)

        return values

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
