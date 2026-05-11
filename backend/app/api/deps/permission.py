from collections.abc import Callable
from dataclasses import dataclass
import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.api.deps.db import get_db_session
from app.core.exceptions import forbidden, not_found
from app.models.user_account import UserAccount
from app.repositories.collaborator_repository import CollaboratorRepository
from app.repositories.family_tree_repository import FamilyTreeRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TreePermissionContext:
    tree_id: int
    user_id: int
    role: str


def _require_tree_role(*allowed_roles: str) -> Callable[..., TreePermissionContext]:
    async def dependency(
        tree_id: int,
        current_user: UserAccount = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_db_session),
    ) -> TreePermissionContext:
        family_tree_repository = FamilyTreeRepository(session)
        collaborator_repository = CollaboratorRepository(session)

        tree = await family_tree_repository.get_by_id(tree_id)
        if tree is None:
            raise not_found("Family tree not found")

        role: str | None
        if tree.creator_user_id == current_user.user_id:
            role = "creator"
        else:
            role = await collaborator_repository.get_active_role(tree_id=tree_id, user_id=current_user.user_id)
            if role is None and "reader" in allowed_roles:
                role = "reader"

        if role is None:
            logger.warning(
                "permission_denied reason=no_tree_access tree_id=%s user_id=%s allowed_roles=%s",
                tree_id,
                current_user.user_id,
                ",".join(allowed_roles),
            )
            raise forbidden("You do not have access to this family tree")
        if role not in allowed_roles:
            logger.warning(
                "permission_denied reason=role_mismatch tree_id=%s user_id=%s role=%s allowed_roles=%s",
                tree_id,
                current_user.user_id,
                role,
                ",".join(allowed_roles),
            )
            raise forbidden("You do not have permission to perform this action")

        return TreePermissionContext(tree_id=tree_id, user_id=current_user.user_id, role=role)

    return dependency


require_tree_reader = _require_tree_role("creator", "collaborator", "reader")
require_tree_editor = _require_tree_role("creator", "collaborator")
require_tree_creator = _require_tree_role("creator")
