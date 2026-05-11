from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.models.family_tree import FamilyTree
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


async def _create_tree(db_session, *, creator_user_id: int, tree_name: str = "Chen Family") -> FamilyTree:
    tree = FamilyTree(
        tree_name=tree_name,
        surname="Chen",
        creator_user_id=creator_user_id,
        description="test tree",
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


async def test_register_returns_session_and_hashes_password(client, db_session):
    username = _unique("new_user")
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "Password123",
            "display_name": "New User",
            "email": f"{username}@example.com",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["username"] == username
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["expires_in"] > 0

    stored_user = await db_session.get(UserAccount, payload["user"]["user_id"])
    assert stored_user is not None
    assert stored_user.password_hash != "Password123"


async def test_register_rejects_duplicate_username(client, db_session):
    username = _unique("duplicate_user")
    await _create_user(db_session, username=username, email=f"{username}@example.com")

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "Password123",
            "display_name": "Another User",
            "email": f"another_{username}@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "USERNAME_ALREADY_EXISTS"


async def test_login_me_refresh_and_logout_flow(client, db_session):
    username = _unique("login_user")
    await _create_user(
        db_session,
        username=username,
        password="Password123",
        display_name="Login User",
        email=f"{username}@example.com",
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Password123"},
    )
    assert login_response.status_code == 200

    session_payload = login_response.json()
    access_token = session_payload["access_token"]
    refresh_token = session_payload["refresh_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == username

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["refresh_token"] != refresh_token

    reused_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused_refresh_response.status_code == 401
    assert reused_refresh_response.json()["code"] == "TOKEN_REVOKED"

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert logout_response.status_code == 200

    revoked_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert revoked_refresh_response.status_code == 401
    assert revoked_refresh_response.json()["code"] == "TOKEN_REVOKED"


async def test_login_rejects_invalid_password_and_disabled_user(client, db_session):
    active_username = _unique("active_user")
    disabled_username = _unique("disabled_user")
    await _create_user(
        db_session,
        username=active_username,
        password="Password123",
        email=f"{active_username}@example.com",
    )
    await _create_user(
        db_session,
        username=disabled_username,
        password="Password123",
        email=f"{disabled_username}@example.com",
        status="disabled",
    )

    bad_password_response = await client.post(
        "/api/v1/auth/login",
        json={"username": active_username, "password": "WrongPass123"},
    )
    assert bad_password_response.status_code == 401
    assert bad_password_response.json()["code"] == "INVALID_CREDENTIALS"

    disabled_user_response = await client.post(
        "/api/v1/auth/login",
        json={"username": disabled_username, "password": "Password123"},
    )
    assert disabled_user_response.status_code == 403
    assert disabled_user_response.json()["code"] == "USER_DISABLED"


async def test_me_rejects_missing_and_wrong_token_type(client, db_session):
    username = _unique("token_user")
    user = await _create_user(
        db_session,
        username=username,
        password="Password123",
        email=f"{username}@example.com",
    )

    missing_token_response = await client.get("/api/v1/auth/me")
    assert missing_token_response.status_code == 401
    assert missing_token_response.json()["code"] == "AUTHENTICATION_REQUIRED"

    wrong_type_token = create_access_token(str(user.user_id)).token
    wrong_type_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": wrong_type_token},
    )
    assert wrong_type_response.status_code == 401
    assert wrong_type_response.json()["code"] == "TOKEN_INVALID"


async def test_family_tree_permissions_for_reader_editor_creator(client, db_session):
    creator_username = _unique("creator_user")
    collaborator_username = _unique("collab_user")
    reader_username = _unique("reader_user")
    outsider_username = _unique("outsider_user")
    creator = await _create_user(db_session, username=creator_username, email=f"{creator_username}@example.com")
    collaborator = await _create_user(db_session, username=collaborator_username, email=f"{collaborator_username}@example.com")
    reader = await _create_user(db_session, username=reader_username, email=f"{reader_username}@example.com")
    outsider = await _create_user(db_session, username=outsider_username, email=f"{outsider_username}@example.com")
    tree = await _create_tree(db_session, creator_user_id=creator.user_id)
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=collaborator.user_id,
        invited_by=creator.user_id,
        access_role="collaborator",
    )
    await _grant_role(
        db_session,
        tree_id=tree.tree_id,
        user_id=reader.user_id,
        invited_by=creator.user_id,
        access_role="reader",
    )

    creator_token = (await client.post("/api/v1/auth/login", json={"username": creator_username, "password": "Password123"})).json()[
        "access_token"
    ]
    collaborator_token = (
        await client.post("/api/v1/auth/login", json={"username": collaborator_username, "password": "Password123"})
    ).json()["access_token"]
    reader_token = (await client.post("/api/v1/auth/login", json={"username": reader_username, "password": "Password123"})).json()[
        "access_token"
    ]
    outsider_token = (
        await client.post("/api/v1/auth/login", json={"username": outsider_username, "password": "Password123"})
    ).json()["access_token"]

    readable_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert readable_response.status_code == 200
    assert readable_response.json()["tree_id"] == tree.tree_id

    collaborator_patch_response = await client.patch(
        f"/api/v1/family-trees/{tree.tree_id}",
        headers={"Authorization": f"Bearer {collaborator_token}"},
    )
    assert collaborator_patch_response.status_code == 200
    assert collaborator_patch_response.json()["access_role"] == "collaborator"

    reader_patch_response = await client.patch(
        f"/api/v1/family-trees/{tree.tree_id}",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert reader_patch_response.status_code == 403
    assert reader_patch_response.json()["code"] == "PERMISSION_DENIED"

    creator_delete_response = await client.delete(
        f"/api/v1/family-trees/{tree.tree_id}",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert creator_delete_response.status_code == 200
    assert creator_delete_response.json()["message"] == f"Family tree {tree.tree_id} deleted"

    outsider_get_response = await client.get(
        f"/api/v1/family-trees/{tree.tree_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert outsider_get_response.status_code == 404
    assert outsider_get_response.json()["code"] == "NOT_FOUND"


async def test_accessible_family_trees_requires_authentication(client, db_session):
    username = _unique("tree_user")
    user = await _create_user(db_session, username=username, email=f"{username}@example.com")
    await _create_tree(db_session, creator_user_id=user.user_id, tree_name="Visible Tree")

    anonymous_response = await client.get("/api/v1/family-trees/accessible")
    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "AUTHENTICATION_REQUIRED"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Password123"},
    )
    access_token = login_response.json()["access_token"]

    accessible_response = await client.get(
        "/api/v1/family-trees/accessible",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert accessible_response.status_code == 200
    assert accessible_response.json()["items"][0]["access_role"] == "creator"
