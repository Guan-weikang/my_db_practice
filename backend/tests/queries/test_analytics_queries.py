from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
from app.models.marriage import Marriage
from app.models.member import Member
from app.models.user_account import UserAccount
from app.queries.analytics_queries import (
    BEFORE_GENERATION_AVERAGE_BIRTH_YEAR_QUERY,
    DASHBOARD_QUERY,
    MAX_AVERAGE_LIFESPAN_QUERY,
    OLDER_THAN_50_UNMARRIED_MALE_QUERY,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


async def _create_user(db_session, *, username: str) -> UserAccount:
    user = UserAccount(
        username=username,
        password_hash=hash_password("Password123"),
        display_name="Test User",
        email=f"{username}@example.com",
        status="active",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str) -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="analytics query test tree",
    )
    db_session.add(tree)
    await db_session.flush()
    await db_session.commit()
    return tree


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


async def test_dashboard_query_returns_counts_and_ratios(db_session):
    creator = await _create_user(db_session, username=_unique("analytics_query_owner"))
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Analytics Query Dashboard Tree")

    await _create_member(db_session, tree_id=tree.tree_id, name="Male One", gender="male")
    await _create_member(db_session, tree_id=tree.tree_id, name="Female One", gender="female")
    await _create_member(db_session, tree_id=tree.tree_id, name="Unknown One", gender="unknown")

    result = await db_session.execute(text(DASHBOARD_QUERY), {"tree_id": tree.tree_id})
    row = dict(result.one()._mapping)

    assert row["tree_id"] == tree.tree_id
    assert row["total_members"] == 3
    assert row["male_count"] == 1
    assert row["female_count"] == 1
    assert row["unknown_count"] == 1
    assert float(row["male_ratio"]) == 0.3333
    assert float(row["female_ratio"]) == 0.3333


async def test_max_average_lifespan_query_prefers_lower_generation_on_tie(db_session):
    creator = await _create_user(db_session, username=_unique("analytics_life_owner"))
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Analytics Query Lifespan Tree")

    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen1 A",
        gender="male",
        birth_date="1940-01-01",
        death_date="2000-01-01",
        generation_no=1,
        is_alive=False,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen1 B",
        gender="female",
        birth_date="1942-01-01",
        death_date="2002-01-01",
        generation_no=1,
        is_alive=False,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen2 A",
        gender="male",
        birth_date="1970-01-01",
        death_date="2030-01-01",
        generation_no=2,
        is_alive=False,
    )

    result = await db_session.execute(text(MAX_AVERAGE_LIFESPAN_QUERY), {"tree_id": tree.tree_id})
    row = dict(result.one()._mapping)

    assert row["tree_id"] == tree.tree_id
    assert row["generation_no"] == 1
    assert float(row["avg_lifespan_years"]) == 60.0


async def test_older_than_50_unmarried_male_query_excludes_active_and_ended_marriage(db_session):
    creator = await _create_user(db_session, username=_unique("analytics_old_owner"))
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Analytics Query Elder Tree")

    eligible = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Eligible",
        gender="male",
        birth_date="1960-01-01",
        generation_no=1,
    )
    active = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Active Married",
        gender="male",
        birth_date="1961-01-01",
        generation_no=1,
    )
    active_spouse = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Active Spouse",
        gender="female",
        birth_date="1962-01-01",
    )
    ended = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Ended Married",
        gender="male",
        birth_date="1959-01-01",
        generation_no=2,
    )
    ended_spouse = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Ended Spouse",
        gender="female",
        birth_date="1960-01-01",
    )

    await _create_marriage(db_session, tree_id=tree.tree_id, member_id_1=active.member_id, member_id_2=active_spouse.member_id)
    await _create_marriage(
        db_session,
        tree_id=tree.tree_id,
        member_id_1=ended.member_id,
        member_id_2=ended_spouse.member_id,
        status="ended",
    )

    result = await db_session.execute(text(OLDER_THAN_50_UNMARRIED_MALE_QUERY), {"tree_id": tree.tree_id})
    rows = [dict(row._mapping) for row in result.all()]

    assert [row["member_id"] for row in rows] == [eligible.member_id]
    assert rows[0]["generation_no"] == 1
    assert rows[0]["age_years"] > 50


async def test_before_generation_average_birth_year_query_returns_only_early_members(db_session):
    creator = await _create_user(db_session, username=_unique("analytics_birth_owner"))
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Analytics Query Birth Tree")

    early_gen1 = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Early Gen1",
        gender="male",
        birth_date="1940-01-01",
        generation_no=1,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Late Gen1",
        gender="female",
        birth_date="1960-01-01",
        generation_no=1,
    )
    early_gen2 = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Early Gen2",
        gender="male",
        birth_date="1980-01-01",
        generation_no=2,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Mid Gen2",
        gender="female",
        birth_date="1990-01-01",
        generation_no=2,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Late Gen2",
        gender="male",
        birth_date="2000-01-01",
        generation_no=2,
    )

    result = await db_session.execute(text(BEFORE_GENERATION_AVERAGE_BIRTH_YEAR_QUERY), {"tree_id": tree.tree_id})
    rows = [dict(row._mapping) for row in result.all()]

    assert [row["member_id"] for row in rows] == [early_gen1.member_id, early_gen2.member_id]
    assert rows[0]["birth_year"] == 1940
    assert float(rows[0]["avg_birth_year"]) == 1950.0
    assert rows[1]["birth_year"] == 1980
    assert float(rows[1]["avg_birth_year"]) == 1990.0
