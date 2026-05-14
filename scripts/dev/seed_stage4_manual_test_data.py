import asyncio
import os
import sys
from datetime import date, datetime, timezone
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
from app.models.marriage import Marriage
from app.models.member import Member
from app.models.parent_child import ParentChild
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


async def touch_tree(tree: FamilyTree) -> None:
    tree.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)


async def ensure_collaborator(
    session,
    *,
    tree_id: int,
    user_id: int,
    invited_by: int,
    access_role: str,
    status: str = "active",
) -> None:
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


async def ensure_member(
    session,
    *,
    tree_id: int,
    name: str,
    gender: str,
    birth_date: date | None = None,
    death_date: date | None = None,
    is_alive: bool = True,
    generation_no: int | None = None,
    generation_name: str | None = None,
    biography: str | None = None,
) -> Member:
    result = await session.execute(
        select(Member).where(
            Member.tree_id == tree_id,
            Member.name == name,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        member = Member(
            tree_id=tree_id,
            name=name,
            gender=gender,
            birth_date=birth_date,
            death_date=death_date,
            is_alive=is_alive,
            generation_no=generation_no,
            generation_name=generation_name,
            biography=biography,
        )
        session.add(member)
    else:
        member.gender = gender
        member.birth_date = birth_date
        member.death_date = death_date
        member.is_alive = is_alive
        member.generation_no = generation_no
        member.generation_name = generation_name
        member.biography = biography
    await session.flush()
    return member


async def ensure_parent_child(
    session,
    *,
    tree_id: int,
    parent_member_id: int,
    child_member_id: int,
    parent_role: str,
) -> None:
    result = await session.execute(
        select(ParentChild).where(
            ParentChild.tree_id == tree_id,
            ParentChild.parent_member_id == parent_member_id,
            ParentChild.child_member_id == child_member_id,
            ParentChild.parent_role == parent_role,
        )
    )
    relation = result.scalar_one_or_none()
    if relation is None:
        session.add(
            ParentChild(
                tree_id=tree_id,
                parent_member_id=parent_member_id,
                child_member_id=child_member_id,
                parent_role=parent_role,
            )
        )
        await session.flush()


def normalize_marriage_members(member_id_1: int, member_id_2: int) -> tuple[int, int]:
    return (member_id_1, member_id_2) if member_id_1 < member_id_2 else (member_id_2, member_id_1)


async def ensure_marriage(
    session,
    *,
    tree_id: int,
    member_id_1: int,
    member_id_2: int,
    married_at: date | None = None,
    ended_at: date | None = None,
    status: str = "active",
) -> None:
    ordered_member_id_1, ordered_member_id_2 = normalize_marriage_members(member_id_1, member_id_2)
    result = await session.execute(
        select(Marriage).where(
            Marriage.tree_id == tree_id,
            Marriage.member_id_1 == ordered_member_id_1,
            Marriage.member_id_2 == ordered_member_id_2,
        )
    )
    marriage = result.scalar_one_or_none()
    if marriage is None:
        marriage = Marriage(
            tree_id=tree_id,
            member_id_1=ordered_member_id_1,
            member_id_2=ordered_member_id_2,
            married_at=married_at,
            ended_at=ended_at,
            status=status,
        )
        session.add(marriage)
    else:
        marriage.married_at = married_at
        marriage.ended_at = ended_at
        marriage.status = status
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
            description="Used for stage4 member and relationship manual testing.",
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

        await touch_tree(managed_tree)
        await touch_tree(empty_tree)
        await touch_tree(public_tree)

        root = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Root Patriarch",
            gender="male",
            birth_date=date(1938, 3, 12),
            death_date=date(2012, 5, 20),
            is_alive=False,
            generation_no=1,
            generation_name="德",
            biography="Three-generation root sample for stage4 testing.",
        )
        matriarch = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Root Matriarch",
            gender="female",
            birth_date=date(1942, 7, 1),
            is_alive=True,
            generation_no=1,
            generation_name="德",
            biography="Root matriarch sample for spouse and parent relationships.",
        )
        son = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Branch Son",
            gender="male",
            birth_date=date(1968, 6, 6),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Second generation branch sample.",
        )
        daughter_in_law = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Daughter In Law",
            gender="female",
            birth_date=date(1970, 8, 18),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Spouse sample for active marriage testing.",
        )
        grandson = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Grandson",
            gender="male",
            birth_date=date(1996, 4, 9),
            is_alive=True,
            generation_no=3,
            generation_name="孝",
            biography="Third generation sample for parent-child testing.",
        )
        granddaughter = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Granddaughter",
            gender="female",
            birth_date=date(1999, 11, 2),
            is_alive=True,
            generation_no=3,
            generation_name="孝",
            biography="Third generation sample for sibling and child-list testing.",
        )
        isolated_member = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Isolated Member",
            gender="unknown",
            birth_date=date(2005, 1, 15),
            is_alive=True,
            generation_no=4,
            generation_name="信",
            biography="No parent-child or marriage relations. Safe to delete in manual tests.",
        )
        ended_husband = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Ended Husband",
            gender="male",
            birth_date=date(1975, 9, 3),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Ended marriage sample.",
        )
        ended_wife = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Ended Wife",
            gender="female",
            birth_date=date(1978, 12, 22),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Ended marriage sample.",
        )

        public_root = await ensure_member(
            session,
            tree_id=public_tree.tree_id,
            name="Stage4 Public Tree Root",
            gender="female",
            birth_date=date(1950, 5, 10),
            is_alive=True,
            generation_no=1,
            generation_name="安",
            biography="Cross-tree sample root for forbidden relationship checks.",
        )

        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=root.member_id,
            child_member_id=son.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=matriarch.member_id,
            child_member_id=son.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=son.member_id,
            child_member_id=grandson.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=daughter_in_law.member_id,
            child_member_id=grandson.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=son.member_id,
            child_member_id=granddaughter.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=daughter_in_law.member_id,
            child_member_id=granddaughter.member_id,
            parent_role="mother",
        )

        await ensure_marriage(
            session,
            tree_id=managed_tree.tree_id,
            member_id_1=root.member_id,
            member_id_2=matriarch.member_id,
            married_at=date(1961, 10, 1),
            status="active",
        )
        await ensure_marriage(
            session,
            tree_id=managed_tree.tree_id,
            member_id_1=son.member_id,
            member_id_2=daughter_in_law.member_id,
            married_at=date(1992, 2, 14),
            status="active",
        )
        await ensure_marriage(
            session,
            tree_id=managed_tree.tree_id,
            member_id_1=ended_husband.member_id,
            member_id_2=ended_wife.member_id,
            married_at=date(2000, 5, 1),
            ended_at=date(2018, 9, 30),
            status="ended",
        )

        await session.commit()

    print("Seeded stage4 manual test data.")
    print("Users:")
    for user_config in USERS:
        print(f"  - {user_config['username']} / {user_config['password']}")
    print("Trees:")
    print("  - Stage3 Managed Tree")
    print("  - Stage3 Empty Tree")
    print("  - Stage3 Public Read Tree")
    print("Managed tree members:")
    print("  - Stage4 Root Patriarch")
    print("  - Stage4 Root Matriarch")
    print("  - Stage4 Branch Son")
    print("  - Stage4 Daughter In Law")
    print("  - Stage4 Grandson")
    print("  - Stage4 Granddaughter")
    print("  - Stage4 Isolated Member")
    print("  - Stage4 Ended Husband")
    print("  - Stage4 Ended Wife")
    print("Cross-tree sample member:")
    print("  - Stage4 Public Tree Root")


if __name__ == "__main__":
    asyncio.run(main())
