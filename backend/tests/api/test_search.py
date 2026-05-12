from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.family_tree import FamilyTree
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


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str = "Search Test Tree") -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="search test tree",
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
    generation_no: int | None = None,
    generation_name: str | None = None,
    is_alive: bool = True,
) -> Member:
    member = Member(
        tree_id=tree_id,
        name=name,
        gender=gender,
        generation_no=generation_no,
        generation_name=generation_name,
        is_alive=is_alive,
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


async def _login(client, *, username: str, password: str = "Password123") -> str:
    response = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_search_members_returns_ranked_results_with_parent_names(client, db_session):
    creator_username = _unique("search_creator")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id)

    exact_match = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Chen Ming",
        gender="male",
        generation_no=2,
        generation_name="德",
    )
    prefix_match = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="Chen Minghao",
        gender="male",
        generation_no=3,
    )
    later_match = await _create_member(
        db_session,
        tree_id=tree.tree_id,
        name="A-Chen Ming",
        gender="male",
        generation_no=1,
    )
    father = await _create_member(db_session, tree_id=tree.tree_id, name="Father Chen", gender="male", generation_no=1)
    mother = await _create_member(db_session, tree_id=tree.tree_id, name="Mother Lin", gender="female", generation_no=1)
    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=father.member_id,
        child_member_id=exact_match.member_id,
        parent_role="father",
    )
    await _create_parent_child(
        db_session,
        tree_id=tree.tree_id,
        parent_member_id=mother.member_id,
        child_member_id=exact_match.member_id,
        parent_role="mother",
    )

    token = await _login(client, username=creator_username)
    response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/search/members",
        headers={"Authorization": f"Bearer {token}"},
        params={"keyword": "  Chen Ming  ", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert [item["member_id"] for item in payload["items"]] == [
        exact_match.member_id,
        prefix_match.member_id,
        later_match.member_id,
    ]
    assert payload["items"][0]["father_name"] == "Father Chen"
    assert payload["items"][0]["mother_name"] == "Mother Lin"
    assert payload["items"][1]["father_name"] is None


async def test_search_members_allows_reader_and_default_viewer_but_denies_invalid_keyword(client, db_session):
    creator_username = _unique("search_owner")
    reader_username = _unique("search_reader")
    viewer_username = _unique("search_viewer")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    viewer = await _create_user(db_session, username=viewer_username, email=f"{viewer_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Readable Search Tree")
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )
    await _create_member(db_session, tree_id=tree.tree_id, name="Alpha Search", gender="female", generation_no=1)

    reader_token = await _login(client, username=reader_username)
    viewer_token = await _login(client, username=viewer_username)

    reader_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/search/members",
        headers={"Authorization": f"Bearer {reader_token}"},
        params={"keyword": "Search"},
    )
    assert reader_response.status_code == 200
    assert reader_response.json()["total"] == 1

    viewer_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/search/members",
        headers={"Authorization": f"Bearer {viewer_token}"},
        params={"keyword": "Search"},
    )
    assert viewer_response.status_code == 200
    assert viewer_response.json()["total"] == 1

    invalid_keyword_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/search/members",
        headers={"Authorization": f"Bearer {reader_token}"},
        params={"keyword": "A"},
    )
    assert invalid_keyword_response.status_code == 400
    assert invalid_keyword_response.json()["code"] == "BAD_REQUEST"


async def test_search_members_supports_pagination_and_requires_login(client, db_session):
    creator_username = _unique("search_pagination")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id, tree_name="Pagination Search Tree")
    for index in range(3):
        await _create_member(
            db_session,
            tree_id=tree.tree_id,
            name=f"Search Seed {index}",
            gender="unknown",
            generation_no=index + 1,
        )

    token = await _login(client, username=creator_username)

    page_two_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/search/members",
        headers={"Authorization": f"Bearer {token}"},
        params={"keyword": "Search", "page": 2, "page_size": 2},
    )
    assert page_two_response.status_code == 200
    payload = page_two_response.json()
    assert payload["total"] == 3
    assert payload["page"] == 2
    assert payload["page_size"] == 2
    assert len(payload["items"]) == 1

    unauthenticated_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}/search/members",
        params={"keyword": "Search"},
    )
    assert unauthenticated_response.status_code == 401
