from datetime import date
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
from app.models.marriage import Marriage
from app.models.member import Member
from app.models.user_account import UserAccount
from app.services.analytics_service import AnalyticsService

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
        description="analytics service test tree",
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


async def test_analytics_service_returns_empty_shapes_for_empty_tree(db_session):
    creator = await _create_user(db_session, username=_unique("analytics_service_owner"))
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Analytics Service Empty Tree")
    service = AnalyticsService(db_session)

    dashboard = await service.get_dashboard(tree_id=tree.tree_id)
    lifespan = await service.get_max_average_lifespan(tree_id=tree.tree_id)
    older = await service.get_older_than_50_unmarried_male(tree_id=tree.tree_id)
    birth_year = await service.get_before_generation_average_birth_year(tree_id=tree.tree_id)

    assert dashboard.summary.total_members == 0
    assert dashboard.summary.male_ratio is None
    assert dashboard.summary.female_ratio is None
    assert lifespan.item is None
    assert older.items == []
    assert birth_year.items == []


async def test_analytics_service_normalizes_populated_results(db_session):
    creator = await _create_user(db_session, username=_unique("analytics_service_data"))
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Analytics Service Data Tree")

    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen1 Elder",
        gender="male",
        birth_date="1940-01-01",
        death_date="2000-01-01",
        generation_no=1,
        generation_name="德",
        is_alive=False,
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Gen1 Elder B",
        gender="female",
        birth_date="1942-01-01",
        death_date="2002-01-01",
        generation_no=1,
        generation_name="德",
        is_alive=False,
    )
    unmarried = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Eligible Elder",
        gender="male",
        birth_date="1975-01-01",
        generation_no=2,
        generation_name="仁",
    )
    married = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Ended Elder",
        gender="male",
        birth_date="1974-01-01",
        generation_no=2,
        generation_name="仁",
    )
    spouse = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Ended Elder Spouse",
        gender="female",
        birth_date="1976-01-01",
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Early Gen2",
        gender="female",
        birth_date="1980-01-01",
        generation_no=3,
        generation_name="孝",
    )
    await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Late Gen2",
        gender="male",
        birth_date="2000-01-01",
        generation_no=3,
        generation_name="孝",
    )
    await _create_marriage(
        db_session,
        tree_id=tree.tree_id,
        member_id_1=married.member_id,
        member_id_2=spouse.member_id,
        status="ended",
    )

    service = AnalyticsService(db_session)
    dashboard = await service.get_dashboard(tree_id=tree.tree_id)
    lifespan = await service.get_max_average_lifespan(tree_id=tree.tree_id)
    older = await service.get_older_than_50_unmarried_male(tree_id=tree.tree_id)
    birth_year = await service.get_before_generation_average_birth_year(tree_id=tree.tree_id)

    assert dashboard.summary.total_members == 7
    assert dashboard.summary.unknown_count == 0
    assert isinstance(dashboard.summary.male_ratio, float)
    assert lifespan.item is not None
    assert lifespan.item.generation_no == 1
    assert lifespan.item.avg_lifespan_years == 60.0
    older_ids = [item.member_id for item in older.items]
    assert unmarried.member_id in older_ids
    assert married.member_id not in older_ids
    assert any(item.generation_name == "仁" for item in older.items)
    assert any(item.name == "Early Gen2" and item.avg_birth_year == 1990.0 for item in birth_year.items)
    assert all(isinstance(item.birth_year, int) for item in birth_year.items)
