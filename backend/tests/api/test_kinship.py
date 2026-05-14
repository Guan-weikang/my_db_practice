from datetime import date
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
from app.models.marriage import Marriage
from app.models.member import Member
from app.models.parent_child import ParentChild
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


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str = "Kinship Test Tree") -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="kinship test tree",
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


async def _create_parent_child(
    db_session,
    *,
    tree_id: int,
    parent_member_id: int,
    child_member_id: int,
    parent_role: str,
) -> None:
    db_session.add(
        ParentChild(
            tree_id=tree_id,
            parent_member_id=parent_member_id,
            child_member_id=child_member_id,
            parent_role=parent_role,
        )
    )
    await db_session.flush()
    await db_session.commit()


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


async def test_ancestor_query_returns_layered_ancestor_subgraph(client, db_session):
    creator_username = _unique("ancestor_creator")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id)

    grandfather = await _create_member(db_session, tree_id=tree.tree_id, name="Grandfather", gender="male", generation_no=1)
    grandmother = await _create_member(db_session, tree_id=tree.tree_id, name="Grandmother", gender="female", generation_no=1)
    father = await _create_member(db_session, tree_id=tree.tree_id, name="Father", gender="male", generation_no=2)
    child = await _create_member(db_session, tree_id=tree.tree_id, name="Child", gender="female", generation_no=3)

    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=father.member_id,
        child_member_id=child.member_id,
        parent_role="father",
    )
    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=grandfather.member_id,
        child_member_id=father.member_id,
        parent_role="father",
    )
    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=grandmother.member_id,
        child_member_id=father.member_id,
        parent_role="mother",
    )

    token = await _login(client, username=creator_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/kinship/ancestors/{child.member_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"max_depth": 10},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["start_member"]["member_id"] == child.member_id
    assert [node["member_id"] for node in payload["nodes"]] == [
        father.member_id,
        grandfather.member_id,
        grandmother.member_id,
    ]
    assert payload["nodes"][0]["depth"] == 1
    assert payload["nodes"][0]["child_member_id"] == child.member_id
    assert payload["nodes"][1]["path_member_ids"] == [child.member_id, father.member_id, grandfather.member_id]


async def test_ancestor_query_allows_reader_and_empty_results(client, db_session):
    creator_username = _unique("ancestor_reader_creator")
    reader_username = _unique("ancestor_reader")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Ancestor Read Tree")
    member = await _create_member(db_session, tree_id=tree.tree_id, name="Solo", gender="male", generation_no=1)
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )

    reader_token = await _login(client, username=reader_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/kinship/ancestors/{member.member_id}",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["start_member"]["member_id"] == member.member_id
    assert payload["nodes"] == []


async def test_kinship_path_returns_nodes_and_edges_and_honors_ended_marriage_flag(client, db_session):
    creator_username = _unique("kinship_creator")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Kinship Path Tree")

    father = await _create_member(db_session, tree_id=tree.tree_id, name="Father", gender="male", generation_no=1)
    child = await _create_member(db_session, tree_id=tree.tree_id, name="Child", gender="male", generation_no=2)
    spouse = await _create_member(db_session, tree_id=tree.tree_id, name="Spouse", gender="female", generation_no=2)
    ex_husband = await _create_member(db_session, tree_id=tree.tree_id, name="Ex Husband", gender="male", generation_no=2)
    outsider = await _create_member(db_session, tree_id=tree.tree_id, name="Outsider", gender="female", generation_no=3)
    isolated = await _create_member(db_session, tree_id=tree.tree_id, name="Isolated", gender="unknown", generation_no=4)

    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=father.member_id,
        child_member_id=child.member_id,
        parent_role="father",
    )
    await _create_marriage(
        db_session,
        tree_id=tree.tree_id,
        member_id_1=child.member_id,
        member_id_2=spouse.member_id,
        status="active",
    )
    await _create_marriage(
        db_session,
        tree_id=tree.tree_id,
        member_id_1=spouse.member_id,
        member_id_2=ex_husband.member_id,
        status="ended",
    )
    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=ex_husband.member_id,
        child_member_id=outsider.member_id,
        parent_role="father",
    )

    token = await _login(client, username=creator_username)

    direct_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/kinship/path",
        headers={"Authorization": f"Bearer {token}"},
        params={"member_a": father.member_id, "member_b": spouse.member_id},
    )
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()
    assert direct_payload["exists"] is True
    assert direct_payload["hop_count"] == 2
    assert [node["member_id"] for node in direct_payload["nodes"]] == [
        father.member_id,
        child.member_id,
        spouse.member_id,
    ]
    assert [edge["relation_type"] for edge in direct_payload["edges"]] == ["parent", "spouse"]
    assert direct_payload["edges"][0]["parent_role"] == "father"
    assert direct_payload["edges"][1]["marriage_status"] == "active"

    no_ended_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/kinship/path",
        headers={"Authorization": f"Bearer {token}"},
        params={"member_a": father.member_id, "member_b": outsider.member_id},
    )
    assert no_ended_response.status_code == 200
    assert no_ended_response.json()["exists"] is False

    with_ended_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/kinship/path",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "member_a": father.member_id,
            "member_b": outsider.member_id,
            "include_ended_marriages": "true",
            "max_depth": 6,
        },
    )
    assert with_ended_response.status_code == 200
    with_ended_payload = with_ended_response.json()
    assert with_ended_payload["exists"] is True
    assert [edge["relation_type"] for edge in with_ended_payload["edges"]] == [
        "parent",
        "spouse",
        "spouse",
        "parent",
    ]
    assert with_ended_payload["edges"][2]["marriage_status"] == "ended"

    same_member_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/kinship/path",
        headers={"Authorization": f"Bearer {token}"},
        params={"member_a": isolated.member_id, "member_b": isolated.member_id},
    )
    assert same_member_response.status_code == 200
    same_member_payload = same_member_response.json()
    assert same_member_payload["exists"] is True
    assert same_member_payload["hop_count"] == 0
    assert len(same_member_payload["nodes"]) == 1
    assert same_member_payload["edges"] == []
