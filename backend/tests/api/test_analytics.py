from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
from app.models.member import Member
from app.models.tree_collaborator import TreeCollaborator
from app.models.user_account import UserAccount

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


async def _create_user(
    db_session,
    *,
    username: str,
    password: str = "Password123",
    display_name: str = "Test User",
    email: str | None = None,
    status: str = "active",
) -> UserAccount:
    user = UserAccount(
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        email=email,
        status=status,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str = "Analytics Test Tree") -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="analytics test tree",
    )
    db_session.add(tree)
    await db_session.flush()
    await db_session.commit()
    return tree


async def _grant_role(db_session, *, tree_id: int, user_id: int, invited_by: int, access_role: str) -> None:
    db_session.add(
        TreeCollaborator(
            tree_id=tree_id,
            user_id=user_id,
            invited_by=invited_by,
            access_role=access_role,
            status="active",
        )
    )
    await db_session.flush()
    await db_session.commit()


async def _create_member(
    db_session,
    *,
    tree_id: int,
    name: str,
    gender: str,
) -> Member:
    member = Member(
        tree_id=tree_id,
        name=name,
        gender=gender,
        is_alive=True,
    )
    db_session.add(member)
    await db_session.flush()
    await db_session.commit()
    return member


async def _login(client, *, username: str, password: str = "Password123") -> str:
    response = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_dashboard_returns_summary_counts_and_ratios(client, db_session):
    creator_username = _unique("analytics_creator")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id)

    await _create_member(db_session, tree_id=tree.tree_id, name="Male One", gender="male")
    await _create_member(db_session, tree_id=tree.tree_id, name="Male Two", gender="male")
    await _create_member(db_session, tree_id=tree.tree_id, name="Female One", gender="female")
    await _create_member(db_session, tree_id=tree.tree_id, name="Unknown One", gender="unknown")

    token = await _login(client, username=creator_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tree_id"] == tree.tree_id
    assert payload["summary"] == {
        "total_members": 4,
        "male_count": 2,
        "female_count": 1,
        "unknown_count": 1,
        "male_ratio": 0.5,
        "female_ratio": 0.25,
    }


async def test_dashboard_allows_reader_and_default_viewer(client, db_session):
    creator_username = _unique("analytics_owner")
    reader_username = _unique("analytics_reader")
    viewer_username = _unique("analytics_viewer")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    viewer = await _create_user(db_session, username=viewer_username, email=f"{viewer_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Readable Analytics Tree")

    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )
    await _create_member(db_session, tree_id=tree.tree_id, name="Only Member", gender="male")

    reader_token = await _login(client, username=reader_username)
    viewer_token = await _login(client, username=viewer_username)

    reader_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/dashboard",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert reader_response.status_code == 200
    assert reader_response.json()["summary"]["total_members"] == 1

    viewer_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/dashboard",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_response.status_code == 200
    assert viewer_response.json()["summary"]["total_members"] == 1


async def test_dashboard_handles_empty_tree_and_requires_login(client, db_session):
    creator_username = _unique("analytics_empty")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Empty Analytics Tree")

    token = await _login(client, username=creator_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["summary"] == {
        "total_members": 0,
        "male_count": 0,
        "female_count": 0,
        "unknown_count": 0,
        "male_ratio": None,
        "female_ratio": None,
    }

    unauthenticated_response = await client.get(f"/api/v1/family-trees/{tree.tree_id}/analytics/dashboard")
    assert unauthenticated_response.status_code == 401
