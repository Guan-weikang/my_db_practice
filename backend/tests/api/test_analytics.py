from datetime import date
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
from app.models.marriage import Marriage
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
    birth_date: str | None = None,
    death_date: str | None = None,
    generation_no: int | None = None,
    generation_name: str | None = None,
    is_alive: bool = True,
) -> Member:
    member = Member(
        tree_id=tree_id,
        name=name,
        gender=gender,
        birth_date=date.fromisoformat(birth_date) if birth_date is not None else None,
        death_date=date.fromisoformat(death_date) if death_date is not None else None,
        generation_no=generation_no,
        generation_name=generation_name,
        is_alive=is_alive,
    )
    db_session.add(member)
    await db_session.flush()
    await db_session.commit()
    return member


async def _create_marriage(
    db_session,
    *,
    tree_id: int,
    member_id_1: int,
    member_id_2: int,
    status: str = "active",
) -> None:
    left = min(member_id_1, member_id_2)
    right = max(member_id_1, member_id_2)
    ended_at = date(2020, 1, 1) if status == "ended" else None
    db_session.add(
        Marriage(
            tree_id=tree_id,
            member_id_1=left,
            member_id_2=right,
            status=status,
            ended_at=ended_at,
        )
    )
    await db_session.flush()
    await db_session.commit()


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


async def test_max_average_lifespan_returns_stable_generation_and_empty_item(client, db_session):
    creator_username = _unique("analytics_lifespan")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Lifespan Analytics Tree")
    empty_tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Lifespan Empty Tree")

    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen 1 A",
        gender="male",
        birth_date="1940-01-01",
        death_date="2000-01-01",
        generation_no=1,
        is_alive=False,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen 1 B",
        gender="female",
        birth_date="1942-01-01",
        death_date="2002-01-01",
        generation_no=1,
        is_alive=False,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen 2 A",
        gender="male",
        birth_date="1970-01-01",
        death_date="2030-01-01",
        generation_no=2,
        is_alive=False,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen 3 No Birth",
        gender="female",
        generation_no=3,
    )

    token = await _login(client, username=creator_username)

    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/generation/max-average-lifespan",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tree_id"] == tree.tree_id
    assert payload["item"]["generation_no"] == 1
    assert payload["item"]["avg_lifespan_years"] == 60.0

    empty_response = await client.get(
        f"/api/v1/family-trees/{empty_tree.tree_id}/analytics/generation/max-average-lifespan",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert empty_response.status_code == 200
    assert empty_response.json() == {"tree_id": empty_tree.tree_id, "item": None}


async def test_older_than_50_unmarried_male_excludes_active_and_ended_marriages(client, db_session):
    creator_username = _unique("analytics_unmarried")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Unmarried Analytics Tree")

    eligible = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Eligible Elder",
        gender="male",
        birth_date="1960-01-01",
        generation_no=1,
        generation_name="德",
    )
    active_male = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Active Marriage Elder",
        gender="male",
        birth_date="1961-01-01",
        generation_no=1,
    )
    active_spouse = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Active Spouse",
        gender="female",
        birth_date="1965-01-01",
    )
    ended_male = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Ended Marriage Elder",
        gender="male",
        birth_date="1958-01-01",
        generation_no=2,
    )
    ended_spouse = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Ended Spouse",
        gender="female",
        birth_date="1960-01-01",
    )
    too_young = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Too Young Elder",
        gender="male",
        birth_date="1990-01-01",
        generation_no=3,
    )

    await _create_marriage(
        db_session,
        tree_id=tree.tree_id,
        member_id_1=active_male.member_id,
        member_id_2=active_spouse.member_id,
        status="active",
    )
    await _create_marriage(
        db_session,
        tree_id=tree.tree_id,
        member_id_1=ended_male.member_id,
        member_id_2=ended_spouse.member_id,
        status="ended",
    )

    token = await _login(client, username=creator_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/members/older-than-50-unmarried-male",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tree_id"] == tree.tree_id
    assert [item["member_id"] for item in payload["items"]] == [eligible.member_id]
    assert payload["items"][0]["name"] == "Eligible Elder"
    assert payload["items"][0]["generation_name"] == "德"
    assert payload["items"][0]["age_years"] > 50
    assert active_male.member_id not in [item["member_id"] for item in payload["items"]]
    assert ended_male.member_id not in [item["member_id"] for item in payload["items"]]
    assert too_young.member_id not in [item["member_id"] for item in payload["items"]]


async def test_before_generation_average_birth_year_returns_expected_members(client, db_session):
    creator_username = _unique("analytics_birthyear")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Birth Year Analytics Tree")

    early_gen1 = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Early Gen1",
        gender="male",
        birth_date="1940-01-01",
        generation_no=1,
        generation_name="德",
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Late Gen1",
        gender="female",
        birth_date="1960-01-01",
        generation_no=1,
        generation_name="德",
    )
    early_gen2 = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Early Gen2",
        gender="male",
        birth_date="1980-01-01",
        generation_no=2,
        generation_name="仁",
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Middle Gen2",
        gender="female",
        birth_date="1990-01-01",
        generation_no=2,
        generation_name="仁",
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Late Gen2",
        gender="male",
        birth_date="2000-01-01",
        generation_no=2,
        generation_name="仁",
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="No Birth",
        gender="female",
        generation_no=3,
    )

    token = await _login(client, username=creator_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/analytics/members/before-generation-average-birth-year",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tree_id"] == tree.tree_id
    assert [item["member_id"] for item in payload["items"]] == [early_gen1.member_id, early_gen2.member_id]
    assert payload["items"][0]["birth_year"] == 1940
    assert payload["items"][0]["avg_birth_year"] == 1950.0
    assert payload["items"][1]["birth_year"] == 1980
    assert payload["items"][1]["avg_birth_year"] == 1990.0
