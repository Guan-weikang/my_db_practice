from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import ResponseCache
from app.core.exceptions import conflict, not_found
from app.repositories.collaborator_repository import CollaboratorRepository
from app.repositories.family_tree_repository import FamilyTreeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.collaborator import (
    CollaboratorCreateRequest,
    CollaboratorResponse,
    CollaboratorUpdateRequest,
    PaginatedCollaboratorResponse,
)
from app.services.cache_helpers import invalidate_tree_cache


class CollaboratorService:
    def __init__(self, session: AsyncSession, cache: ResponseCache | None = None) -> None:
        self.session = session
        self.cache = cache
        self.collaborator_repository = CollaboratorRepository(session)
        self.family_tree_repository = FamilyTreeRepository(session)
        self.user_repository = UserRepository(session)

    async def list_for_tree(self, *, tree_id: int, page: int, page_size: int) -> PaginatedCollaboratorResponse:
        await self._ensure_tree_exists(tree_id)
        offset = (page - 1) * page_size
        items = await self.collaborator_repository.list_for_tree(tree_id, offset=offset, limit=page_size)
        total = await self.collaborator_repository.count_for_tree(tree_id)
        return PaginatedCollaboratorResponse(
            items=[CollaboratorResponse(**item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create(
        self,
        *,
        tree_id: int,
        invited_by: int,
        payload: CollaboratorCreateRequest,
    ) -> CollaboratorResponse:
        tree = await self._get_tree_or_raise(tree_id)
        if payload.user_id == invited_by:
            raise conflict("Creator cannot invite themselves as collaborator")
        if payload.user_id == tree.creator_user_id:
            raise conflict("Family tree creator cannot be managed as collaborator")

        user = await self.user_repository.get_by_id(payload.user_id)
        if user is None:
            raise not_found("Target user not found")

        existing = await self.collaborator_repository.get_by_tree_and_user(tree_id=tree_id, user_id=payload.user_id)
        if existing is not None and existing.status == "active":
            raise conflict("Collaborator already has active access to this family tree")

        if existing is None:
            collaborator = await self.collaborator_repository.create(
                tree_id=tree_id,
                user_id=payload.user_id,
                invited_by=invited_by,
                access_role=payload.access_role,
                status="active",
            )
        else:
            collaborator = await self.collaborator_repository.update(
                existing,
                {
                    "access_role": payload.access_role,
                    "status": "active",
                    "invited_by": invited_by,
                },
            )

        await self.session.commit()
        await invalidate_tree_cache(self.cache, tree_id)
        return await self._build_response(tree_id=tree_id, user_id=collaborator.user_id)

    async def update(
        self,
        *,
        tree_id: int,
        user_id: int,
        payload: CollaboratorUpdateRequest,
    ) -> CollaboratorResponse:
        tree = await self._get_tree_or_raise(tree_id)
        if user_id == tree.creator_user_id:
            raise conflict("Family tree creator role cannot be modified through collaborator management")

        collaborator = await self.collaborator_repository.get_by_tree_and_user(tree_id=tree_id, user_id=user_id)
        if collaborator is None:
            raise not_found("Collaborator not found")

        await self.collaborator_repository.update(
            collaborator,
            {
                "access_role": payload.access_role,
                "status": "active",
            },
        )
        await self.session.commit()
        await invalidate_tree_cache(self.cache, tree_id)
        return await self._build_response(tree_id=tree_id, user_id=user_id)

    async def revoke(self, *, tree_id: int, user_id: int) -> None:
        tree = await self._get_tree_or_raise(tree_id)
        if user_id == tree.creator_user_id:
            raise conflict("Family tree creator cannot be revoked through collaborator management")

        collaborator = await self.collaborator_repository.get_by_tree_and_user(tree_id=tree_id, user_id=user_id)
        if collaborator is None:
            raise not_found("Collaborator not found")

        await self.collaborator_repository.update(
            collaborator,
            {
                "status": "revoked",
            },
        )
        await self.session.commit()
        await invalidate_tree_cache(self.cache, tree_id)

    async def _build_response(self, *, tree_id: int, user_id: int) -> CollaboratorResponse:
        items = await self.collaborator_repository.list_for_tree(tree_id, offset=0, limit=1000)
        for item in items:
            if item["user_id"] == user_id:
                return CollaboratorResponse(**item)
        raise not_found("Collaborator not found")

    async def _ensure_tree_exists(self, tree_id: int) -> None:
        await self._get_tree_or_raise(tree_id)

    async def _get_tree_or_raise(self, tree_id: int):
        tree = await self.family_tree_repository.get_by_id(tree_id)
        if tree is None:
            raise not_found("Family tree not found")
        return tree
