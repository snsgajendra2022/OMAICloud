"""Account register / login / logout with HttpOnly cookie sessions."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_account_cookie_session_and_chats(tmp_path: Path, monkeypatch):
    accounts = tmp_path / "accounts.sqlite3"
    chats = tmp_path / "om_ai.sqlite3"
    monkeypatch.setenv("OM_AI_ACCOUNTS_DB", str(accounts))
    monkeypatch.setenv("OM_AI_DB", str(chats))
    monkeypatch.setenv("OM_AI_REQUIRE_AUTH", "1")
    monkeypatch.setenv("OM_AI_API_KEYS", "bootstrap-test-key:admin")
    monkeypatch.setenv("OM_AI_AUTOLOAD", "0")
    monkeypatch.setenv("OM_AI_ALLOW_REGISTER", "1")

    import om_ai.security.accounts as accounts_mod
    import om_ai.security.auth as auth_mod
    import om_ai.api.conversations as conv_mod

    accounts_mod._store = None
    auth_mod._auth_instance = None
    conv_mod._store = None

    from om_ai.api.main import app
    from om_ai.memory.conversations import ConversationStore
    from om_ai.api.conversations import bind_conversation_store

    bind_conversation_store(ConversationStore(str(chats)))

    client = TestClient(app)

    status = client.get("/v1/auth/status")
    assert status.status_code == 200
    assert status.json()["cookie_auth"] is True

    reg = client.post(
        "/v1/auth/register",
        json={
            "email": "brain@example.com",
            "password": "secret123",
            "display_name": "Brain",
        },
    )
    assert reg.status_code == 201, reg.text
    assert "om_session" in reg.cookies
    assert reg.json()["user"]["email"] == "brain@example.com"

    me = client.get("/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["account"] is True
    assert me.json()["actor"].startswith("user:")

    created = client.post("/v1/conversations", json={"title": "hello brain"})
    assert created.status_code == 201, created.text
    cid = created.json()["id"]
    assert created.json().get("user_id")

    listed = client.get("/v1/conversations")
    assert listed.status_code == 200
    ids = [c["id"] for c in listed.json()["conversations"]]
    assert cid in ids

    got = client.get(f"/v1/conversations/{cid}")
    assert got.status_code == 200
    assert got.json()["id"] == cid

    me2 = client.get("/v1/auth/me")
    assert me2.json().get("last_conversation_id") == cid

    out = client.post("/v1/auth/logout")
    assert out.status_code == 200
    dead = client.get("/v1/auth/me")
    assert dead.status_code == 401

    # Other account cannot see first user's chats
    client.post(
        "/v1/auth/register",
        json={"email": "other@example.com", "password": "secret123", "display_name": "Other"},
    )
    listed2 = client.get("/v1/conversations")
    assert listed2.status_code == 200
    assert listed2.json()["conversations"] == []
