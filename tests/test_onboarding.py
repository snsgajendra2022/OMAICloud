"""Onboarding bootstrap creates workspace defaults for new logins."""
from __future__ import annotations

from om_ai.api.onboarding import bootstrap_user_workspace
from om_ai.api.platform_store import PlatformStore
from om_ai.api.workspace_store import WorkspaceStore
from om_ai.memory.conversations import ConversationStore


def test_bootstrap_creates_defaults(tmp_path, monkeypatch):
    pdb = tmp_path / "platform.db"
    cdb = tmp_path / "chat.db"
    wdb = tmp_path / "ws.db"

    pstore = PlatformStore(str(pdb))
    pstore.upload_root = tmp_path / "uploads"
    pstore.upload_root.mkdir(parents=True, exist_ok=True)
    cstore = ConversationStore(str(cdb))
    wstore = WorkspaceStore(str(wdb))

    monkeypatch.setattr("om_ai.api.platform_store.get_platform_store", lambda: pstore)
    monkeypatch.setattr("om_ai.api.conversations.get_store", lambda: cstore)
    monkeypatch.setattr("om_ai.api.workspace_store.get_workspace_store", lambda: wstore)

    actor = "user:test-onboard"
    tenant = "default"
    out = bootstrap_user_workspace(tenant, actor, display_name="Gajendra")
    assert out["ok"] is True
    assert out["created"]["welcome_chat"] is True
    assert out["created"]["assistant"] is True
    assert out["created"]["library"] >= 1
    assert out["created"]["prompts"] >= 1
    assert out["created"]["memory"] is True

    # Idempotent — second call does not duplicate
    out2 = bootstrap_user_workspace(tenant, actor, display_name="Gajendra")
    assert out2["ok"] is True
    assert out2["created"]["welcome_chat"] is False
    assert out2["created"]["assistant"] is False
    assert out2["created"]["library"] == 0

    assert len(cstore.list_conversations(tenant, actor)) >= 1
    assert len(wstore.list_assistants(tenant, actor)) >= 1
    assert len(pstore.list_library(tenant, actor)) >= 1
    assert len(pstore.list_prompts(tenant, actor)) >= 1
    assert len(pstore.list_memories(tenant, actor)) >= 1


def test_compose_fallback_feels_human():
    from om_ai.agent.verifier import compose_fallback

    g = compose_fallback(intent="greeting", user_text="namaste")
    assert "OM" in g
    assert len(g) > 20

    sad = compose_fallback(intent="chat", user_text="I feel sad today")
    assert "sorry" in sad.lower() or "with you" in sad.lower()
