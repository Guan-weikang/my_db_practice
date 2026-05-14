import asyncio
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:123456@localhost:5432/family_tree_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "dev-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "dev-refresh-secret")
os.environ.setdefault("APP_ENV", "development")

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.family_tree import FamilyTree
from app.models.member import Member
from app.models.tree_collaborator import TreeCollaborator
from app.models.user_account import UserAccount


USERS = [
    {
        "username": "stage3_creator",
        "password": "Password123",
        "display_name": "Stage3 Creator",
        "email": "stage3_creator@example.com",
    },
    {
        "username": "stage3_collaborator",
        "password": "Password123",
        "display_name": "Stage3 Collaborator",
        "email": "stage3_collaborator@example.com",
    },
    {
        "username": "stage3_reader",
        "password": "Password123",
        "display_name": "Stage3 Reader",
        "email": "stage3_reader@example.com",
    },
    {
        "username": "stage3_viewer",
        "password": "Password123",
        "display_name": "Stage3 Viewer",
        "email": "stage3_viewer@example.com",
    },
]


async def get_or_create_user(session, user_config: dict) -> UserAccount:
    result = await session.execute(select(UserAccount).where(UserAccount.username == user_config["username"]))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = UserAccount(
        username=user_config["username"],
        password_hash=hash_password(user_config["password"]),
        display_name=user_config["display_name"],
        email=user_config["email"],
        status="active",
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_tree(session, *, creator_user_id: int, tree_name: str, surname: str, description: str) -> FamilyTree:
    result = await session.execute(
        select(FamilyTree).where(
            FamilyTree.creator_user_id == creator_user_id,
            FamilyTree.tree_name == tree_name,
        )
    )
    tree = result.scalar_one_or_none()
    if tree is not None:
        return tree

    tree = FamilyTree(
        tree_name=tree_name,
        surname=surname,
        creator_user_id=creator_user_id,
        description=description,
    )
    session.add(tree)
    await session.flush()
    return tree


async def ensure_member(session, *, tree_id: int, name: str, gender: str = "unknown") -> None:
    result = await session.execute(
        select(Member).where(
            Member.tree_id == tree_id,
            Member.name == name,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        session.add(
            Member(
                tree_id=tree_id,
                name=name,
                gender=gender,
                is_alive=True,
            )
        )
        await session.flush()


async def ensure_collaborator(session, *, tree_id: int, user_id: int, invited_by: int, access_role: str, status: str = "active") -> None:
    result = await session.execute(
        select(TreeCollaborator).where(
            TreeCollaborator.tree_id == tree_id,
            TreeCollaborator.user_id == user_id,
        )
    )
    collaborator = result.scalar_one_or_none()
    if collaborator is None:
        collaborator = TreeCollaborator(
            tree_id=tree_id,
            user_id=user_id,
            invited_by=invited_by,
            access_role=access_role,
            status=status,
        )
        session.add(collaborator)
    else:
        collaborator.access_role = access_role
        collaborator.status = status
        collaborator.invited_by = invited_by
    await session.flush()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        seeded_users: dict[str, UserAccount] = {}
        for user_config in USERS:
            user = await get_or_create_user(session, user_config)
            seeded_users[user.username] = user

        creator = seeded_users["stage3_creator"]
        collaborator = seeded_users["stage3_collaborator"]
        reader = seeded_users["stage3_reader"]
        viewer = seeded_users["stage3_viewer"]

        managed_tree = await get_or_create_tree(
            session,
            creator_user_id=creator.user_id,
            tree_name="Stage3 Managed Tree",
            surname="Chen",
            description="Used for collaborator management and edit testing.",
        )
        empty_tree = await get_or_create_tree(
            session,
            creator_user_id=creator.user_id,
            tree_name="Stage3 Empty Tree",
            surname="Chen",
            description="Used for empty-tree delete testing.",
        )
        public_tree = await get_or_create_tree(
            session,
            creator_user_id=viewer.user_id,
            tree_name="Stage3 Public Read Tree",
            surname="Li",
            description="Used to verify default readable behavior for all logged-in users.",
        )

        await ensure_member(session, tree_id=managed_tree.tree_id, name="Managed Tree Root", gender="male")
        await ensure_member(session, tree_id=public_tree.tree_id, name="Public Tree Root", gender="female")

        await ensure_collaborator(
            session,
            tree_id=managed_tree.tree_id,
            user_id=collaborator.user_id,
            invited_by=creator.user_id,
            access_role="collaborator",
            status="active",
        )
        await ensure_collaborator(
            session,
            tree_id=managed_tree.tree_id,
            user_id=reader.user_id,
            invited_by=creator.user_id,
            access_role="reader",
            status="active",
        )

        await session.commit()

    print("Seeded stage3 manual test data.")
    print("Users:")
    for user_config in USERS:
        print(f"  - {user_config['username']} / {user_config['password']}")
    print("Trees:")
    print("  - Stage3 Managed Tree")
    print("  - Stage3 Empty Tree")
    print("  - Stage3 Public Read Tree")


if __name__ == "__main__":
    asyncio.run(main())
