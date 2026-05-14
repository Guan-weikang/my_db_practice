from datetime import date
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
from app.models.user_account import UserAccount
from app.models.tree_collaborator import TreeCollaborator
from app.models.member import Member

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


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str = "Relationship Test Tree") -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="relationship test tree",
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
    generation_no: int | None = None,
) -> Member:
    member = Member(
        tree_id=tree_id,
        name=name,
        gender=gender,
        birth_date=date.fromisoformat(birth_date) if birth_date is not None else None,
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


async def test_parent_child_flow_and_member_delete_cascade(client, db_session):
    creator_username = _unique("rel_creator")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id)
    father = await _create_member(db_session, tree_id=tree.tree_id, name="Father", gender="male", birth_date="1960-01-01")
    mother = await _create_member(db_session, tree_id=tree.tree_id, name="Mother", gender="female", birth_date="1962-01-01")
    child = await _create_member(db_session, tree_id=tree.tree_id, name="Child", gender="male", birth_date="1990-01-01")
    spouse = await _create_member(db_session, tree_id=tree.tree_id, name="Spouse", gender="female", birth_date="1991-01-01")

    token = await _login(client, username=creator_username)

    father_relation_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {token}"},
        json={"parent_member_id": father.member_id, "child_member_id": child.member_id, "parent_role": "father"},
    )
    assert father_relation_response.status_code == 200

    mother_relation_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {token}"},
        json={"parent_member_id": mother.member_id, "child_member_id": child.member_id, "parent_role": "mother"},
    )
    assert mother_relation_response.status_code == 200

    marriage_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {token}"},
        json={"member_id_1": child.member_id, "member_id_2": spouse.member_id, "married_at": "2015-01-01"},
    )
    assert marriage_response.status_code == 200

    parents_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{child.member_id}/parents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert parents_response.status_code == 200
    assert {item["parent_role"] for item in parents_response.json()} == {"father", "mother"}

    children_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{father.member_id}/children",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert children_response.status_code == 200
    assert children_response.json()[0]["child_member_id"] == child.member_id

    spouses_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{child.member_id}/spouses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert spouses_response.status_code == 200
    assert spouses_response.json()[0]["spouse_member_id"] == spouse.member_id

    delete_member_response = await client.delete(
        f"/api/v1/family-trees/{tree.tree_id}/members/{child.member_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_member_response.status_code == 200

    parents_after_delete = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{father.member_id}/children",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert parents_after_delete.status_code == 200
    assert parents_after_delete.json() == []

    spouses_after_delete = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{spouse.member_id}/spouses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert spouses_after_delete.status_code == 200
    assert spouses_after_delete.json() == []


async def test_parent_child_conflicts_and_reader_permissions(client, db_session):
    creator_username = _unique("pc_creator")
    reader_username = _unique("pc_reader")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Parent Child Conflict Tree")
    grandfather = await _create_member(db_session, tree_id=tree.tree_id, name="Grandfather", gender="male", birth_date="1940-01-01")
    father = await _create_member(db_session, tree_id=tree.tree_id, name="Father", gender="male", birth_date="1970-01-01")
    child = await _create_member(db_session, tree_id=tree.tree_id, name="Child", gender="male", birth_date="2000-01-01")
    younger_parent = await _create_member(db_session, tree_id=tree.tree_id, name="Younger", gender="female", birth_date="2010-01-01")
    invalid_mother = await _create_member(db_session, tree_id=tree.tree_id, name="Invalid Mother", gender="male", birth_date="1965-01-01")
    invalid_father = await _create_member(db_session, tree_id=tree.tree_id, name="Invalid Father", gender="female", birth_date="1965-01-01")
    cycle_root = await _create_member(db_session, tree_id=tree.tree_id, name="Cycle Root", gender="male")
    cycle_mid = await _create_member(db_session, tree_id=tree.tree_id, name="Cycle Mid", gender="female")
    cycle_leaf = await _create_member(db_session, tree_id=tree.tree_id, name="Cycle Leaf", gender="male")

    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )

    creator_token = await _login(client, username=creator_username)
    reader_token = await _login(client, username=reader_username)

    first_relation = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": father.member_id, "child_member_id": child.member_id, "parent_role": "father"},
    )
    assert first_relation.status_code == 200

    duplicate_father = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": grandfather.member_id, "child_member_id": child.member_id, "parent_role": "father"},
    )
    assert duplicate_father.status_code == 409

    invalid_birth_order = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": younger_parent.member_id, "child_member_id": child.member_id, "parent_role": "mother"},
    )
    assert invalid_birth_order.status_code == 400

    invalid_mother_gender = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": invalid_mother.member_id, "child_member_id": child.member_id, "parent_role": "mother"},
    )
    assert invalid_mother_gender.status_code == 400

    invalid_father_gender = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": invalid_father.member_id, "child_member_id": child.member_id, "parent_role": "father"},
    )
    assert invalid_father_gender.status_code == 400

    grandparent_relation = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": grandfather.member_id, "child_member_id": father.member_id, "parent_role": "father"},
    )
    assert grandparent_relation.status_code == 200

    cycle_relation_a = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": cycle_root.member_id, "child_member_id": cycle_mid.member_id, "parent_role": "father"},
    )
    assert cycle_relation_a.status_code == 200

    cycle_relation_b = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": cycle_mid.member_id, "child_member_id": cycle_leaf.member_id, "parent_role": "mother"},
    )
    assert cycle_relation_b.status_code == 200

    cycle_attempt = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"parent_member_id": cycle_leaf.member_id, "child_member_id": cycle_root.member_id, "parent_role": "father"},
    )
    assert cycle_attempt.status_code == 409

    reader_write_attempt = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/parent-child",
        headers={"Authorization": f"Bearer {reader_token}"},
        json={"parent_member_id": grandfather.member_id, "child_member_id": child.member_id, "parent_role": "mother"},
    )
    assert reader_write_attempt.status_code == 403


async def test_marriage_flow_conflicts_and_permissions(client, db_session):
    creator_username = _unique("mar_creator")
    reader_username = _unique("mar_reader")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Marriage Tree")
    member_a = await _create_member(db_session, tree_id=tree.tree_id, name="A", gender="male", birth_date="1985-01-01")
    member_b = await _create_member(db_session, tree_id=tree.tree_id, name="B", gender="female", birth_date="1986-01-01")
    member_c = await _create_member(db_session, tree_id=tree.tree_id, name="C", gender="male", birth_date="1987-01-01")
    member_d = await _create_member(db_session, tree_id=tree.tree_id, name="D", gender="unknown", birth_date="1988-01-01")
    member_e = await _create_member(db_session, tree_id=tree.tree_id, name="E", gender="female", birth_date="1990-01-01")

    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )

    creator_token = await _login(client, username=creator_username)
    reader_token = await _login(client, username=reader_username)

    create_response = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_b.member_id, "member_id_2": member_a.member_id, "married_at": "2010-05-01"},
    )
    assert create_response.status_code == 200
    marriage_payload = create_response.json()
    assert marriage_payload["member_id_1"] == min(member_a.member_id, member_b.member_id)
    assert marriage_payload["member_id_2"] == max(member_a.member_id, member_b.member_id)
    assert marriage_payload["status"] == "active"

    spouses_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{member_a.member_id}/spouses",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert spouses_response.status_code == 200
    assert spouses_response.json()[0]["spouse_member_id"] == member_b.member_id

    duplicate_active_spouse = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_a.member_id, "member_id_2": member_e.member_id},
    )
    assert duplicate_active_spouse.status_code == 409

    update_response = await client.patch(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "member_id_1": member_a.member_id,
            "member_id_2": member_b.member_id,
            "ended_at": "2020-05-01",
            "status": "ended",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "ended"
    assert update_response.json()["ended_at"] == "2020-05-01"

    duplicate_create = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_a.member_id, "member_id_2": member_b.member_id},
    )
    assert duplicate_create.status_code == 409

    self_marriage = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_a.member_id, "member_id_2": member_a.member_id},
    )
    assert self_marriage.status_code == 409

    same_gender_marriage = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_a.member_id, "member_id_2": member_c.member_id},
    )
    assert same_gender_marriage.status_code == 400

    unknown_gender_marriage = await client.post(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_a.member_id, "member_id_2": member_d.member_id},
    )
    assert unknown_gender_marriage.status_code == 400

    invalid_dates = await client.patch(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={
            "member_id_1": member_a.member_id,
            "member_id_2": member_b.member_id,
            "married_at": "2021-01-01",
            "ended_at": "2020-01-01",
            "status": "ended",
        },
    )
    assert invalid_dates.status_code == 400

    reader_write_attempt = await client.request(
        "DELETE",
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {reader_token}"},
        json={"member_id_1": member_a.member_id, "member_id_2": member_b.member_id},
    )
    assert reader_write_attempt.status_code == 403

    delete_response = await client.request(
        "DELETE",
        f"/api/v1/family-trees/{tree.tree_id}/relationships/marriages",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"member_id_1": member_b.member_id, "member_id_2": member_a.member_id},
    )
    assert delete_response.status_code == 200

    spouses_after_delete = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/relationships/members/{member_a.member_id}/spouses",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert spouses_after_delete.status_code == 200
    assert spouses_after_delete.json() == []
