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


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str = "Member Test Tree") -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="member test tree",
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
    gender: str = "unknown",
    generation_no: int | None = None,
) -> Member:
    member = Member(
        tree_id=tree_id,
        name=name,
        gender=gender,
        generation_no=generation_no,
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


async def test_member_crud_flow_for_editor_roles(client, db_session):
    creator_username = _unique("member_creator")
    collaborator_username = _unique("member_collaborator")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    collaborator = await _create_user(
        db_session,
        username=collaborator_username,
        email=f"{collaborator_username}@example.com",
    )
    tree = await _create_tree(db_session, creator_user_id=creator.user_id)
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=collaborator.user_id,
        invited_by=creator.user_id,
        access_role="collaborator",
    )

    creator_token = await _login(client, username=creator_username)
    collaborator_token = await _login(client, username=collaborator_username)

    create_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "name": "  Chen Root  ",
            "gender": "male",
            "birth_date": "1960-01-02",
            "generation_no": 1,
            "generation_name": "  德  ",
            "biography": "  root member  ",
        },
    )
    assert create_response.status_code == 201
    created_member = create_response.json()
    assert created_member["name"] == "Chen Root"
    assert created_member["generation_name"] == "德"
    assert created_member["biography"] == "root member"
    assert created_member["is_alive"] is True

    member_id = created_member["member_id"]

    list_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members?page=1&page_size=10",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1
    assert any(item["member_id"] == member_id for item in list_response.json()["items"])

    detail_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["member_id"] == member_id

    update_response = await client.patch(
        f"/api/v1/family-trees/{tree.tree_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {collaborator_token}"},
        json={
            "name": "  Chen Updated ",
            "generation_name": " 仁 ",
            "biography": " updated biography ",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Chen Updated"
    assert update_response.json()["generation_name"] == "仁"
    assert update_response.json()["biography"] == "updated biography"

    refreshed_member = await db_session.get(Member, member_id)
    assert refreshed_member is not None
    await db_session.refresh(refreshed_member)
    assert refreshed_member.name == "Chen Updated"

    delete_response = await client.delete(
        f"/api/v1/family-trees/{tree.tree_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == f"Member {member_id} deleted from family tree {tree.tree_id}"

    deleted_detail_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert deleted_detail_response.status_code == 404
    assert deleted_detail_response.json()["code"] == "NOT_FOUND"


async def test_member_id_range_returns_tree_bounds_for_reader(client, db_session):
    creator_username = _unique("member_range_creator")
    reader_username = _unique("member_range_reader")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Member Range Tree")
    first_member = await _create_member(db_session, tree_id=tree.tree_id, name="Range First", generation_no=1)
    second_member = await _create_member(db_session, tree_id=tree.tree_id, name="Range Second", generation_no=2)
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )

    reader_token = await _login(client, username=reader_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members/id-range",
        headers={"Authorization": f"Bearer {reader_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "min_member_id": first_member.member_id,
        "max_member_id": second_member.member_id,
        "total": 2,
    }


async def test_member_reading_allowed_but_write_denied_for_reader_and_viewer(client, db_session):
    creator_username = _unique("member_owner")
    reader_username = _unique("member_reader")
    viewer_username = _unique("member_viewer")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    viewer = await _create_user(db_session, username=viewer_username, email=f"{viewer_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Read Only Tree")
    member = await _create_member(db_session, tree_id=tree.tree_id, name="Readable Member", generation_no=2)
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )

    reader_token = await _login(client, username=reader_username)
    viewer_token = await _login(client, username=viewer_username)

    reader_detail_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members/{member.member_id}",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert reader_detail_response.status_code == 200

    viewer_list_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_list_response.status_code == 200
    assert any(item["member_id"] == member.member_id for item in viewer_list_response.json()["items"])

    reader_update_response = await client.patch(
        f"/api/v1/family-trees/{tree.tree_id}/members/{member.member_id}",
        headers={"Authorization": f"Bearer {reader_token}"},
        json={"name": "Should Fail"},
    )
    assert reader_update_response.status_code == 403
    assert reader_update_response.json()["code"] == "PERMISSION_DENIED"

    viewer_create_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "Viewer Create", "gender": "unknown"},
    )
    assert viewer_create_response.status_code == 403
    assert viewer_create_response.json()["code"] == "PERMISSION_DENIED"


async def test_member_validation_and_sorting(client, db_session):
    creator_username = _unique("member_validation")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Validation Tree")
    await _create_member(db_session, tree_id=tree.tree_id, name="Gen2", gender="female", generation_no=2)
    await _create_member(db_session, tree_id=tree.tree_id, name="Gen1", gender="male", generation_no=1)

    creator_token = await _login(client, username=creator_username)

    sorted_list_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert sorted_list_response.status_code == 200
    names = [item["name"] for item in sorted_list_response.json()["items"]]
    assert names[:2] == ["Gen1", "Gen2"]

    empty_name_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"name": "   ", "gender": "unknown"},
    )
    assert empty_name_response.status_code == 400
    assert empty_name_response.json()["code"] == "BAD_REQUEST"

    invalid_gender_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"name": "Invalid Gender", "gender": "other"},
    )
    assert invalid_gender_response.status_code == 400

    invalid_life_span_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "name": "Bad Dates",
            "gender": "unknown",
            "birth_date": "2000-01-01",
            "death_date": "1999-01-01",
            "is_alive": False,
        },
    )
    assert invalid_life_span_response.status_code == 400

    alive_with_death_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/members",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "name": "Alive With Death",
            "gender": "unknown",
            "death_date": "2020-01-01",
            "is_alive": True,
        },
    )
    assert alive_with_death_response.status_code == 400
