"""Tests for ConversationStore (chat history, folders, profile)."""
from __future__ import annotations

import pytest

from om_ai.memory.conversations import ConversationStore, capitalize_title


def test_capitalize_title():
    assert capitalize_title("what year is it") == "What year is it"
    assert capitalize_title("hiiii") == "Hiiii"
    assert capitalize_title("ram ram ji") == "Ram ram ji"
    assert capitalize_title("hello") == "Hello"
    assert capitalize_title("  already Cap") == "Already Cap"
    assert capitalize_title("") == ""


def test_make_chat_title_rejects_assistant_greeting():
    from om_ai.memory.conversations import make_chat_title, _assistant_like_title

    assert _assistant_like_title("Hi! I'm OM AI. How can I help you today?")
    assert make_chat_title("Hi! I'm OM AI. How can I help you today?") == ""
    assert make_chat_title("नमस्ते") == "नमस्ते"
    assert make_chat_title("hiii").startswith("H")


def test_auto_title_repairs_assistant_greeting(tmp_path):
    store = ConversationStore(str(tmp_path / "chat.db"))
    conv = store.create_conversation("t1", "alice", title="Hi! I'm OM AI. How can I help you today?")
    store.append_messages(
        conv.id,
        "t1",
        "alice",
        [
            {"role": "user", "content": "Ram Ram ji"},
            {"role": "assistant", "content": "Hi! I'm OM AI. How can I help you today?"},
        ],
    )
    updated = store.get_conversation(conv.id, "t1", "alice")
    assert updated.title.startswith("Ram")
    listed = store.list_conversations("t1", "alice")
    assert listed[0].title.startswith("Ram")


def test_conversation_crud_and_messages(tmp_path):
    store = ConversationStore(str(tmp_path / "chat.db"))
    conv = store.create_conversation("t1", "alice", title="New chat")
    assert conv.title == "New chat"
    assert conv.message_count == 0

    created = store.append_messages(
        conv.id,
        "t1",
        "alice",
        [
            {"role": "user", "content": "Hello OM, how are you today?"},
            {"role": "assistant", "content": "Doing well."},
        ],
    )
    assert len(created) == 2
    updated = store.get_conversation(conv.id, "t1", "alice")
    assert updated.title.startswith("Hello OM")
    assert updated.message_count == 2

    msgs = store.list_messages(conv.id, "t1", "alice")
    assert [m.role for m in msgs] == ["user", "assistant"]

    store.update_conversation(conv.id, "t1", "alice", title="Renamed")
    assert store.get_conversation(conv.id, "t1", "alice").title == "Renamed"

    store.delete_conversation(conv.id, "t1", "alice")
    with pytest.raises(KeyError):
        store.get_conversation(conv.id, "t1", "alice")


def test_auto_title_and_folder_capitalize_first_letter(tmp_path):
    store = ConversationStore(str(tmp_path / "chat.db"))
    conv = store.create_conversation("t1", "alice")
    store.append_messages(
        conv.id,
        "t1",
        "alice",
        [
            {"role": "user", "content": "what year is it"},
            {"role": "assistant", "content": "2026"},
        ],
    )
    assert store.get_conversation(conv.id, "t1", "alice").title == "What year is it"

    folder = store.create_folder("t1", "alice", "my project")
    assert folder.name == "My project"
    renamed = store.rename_folder(folder.id, "t1", "alice", "side stuff")
    assert renamed.name == "Side stuff"
    updated = store.update_conversation(conv.id, "t1", "alice", title="ram ram ji")
    assert updated.title == "Ram ram ji"


def test_folders_and_move(tmp_path):
    store = ConversationStore(str(tmp_path / "chat.db"))
    folder = store.create_folder("t1", "alice", "Work")
    conv = store.create_conversation("t1", "alice", folder_id=folder.id)
    assert conv.folder_id == folder.id

    listed = store.list_conversations("t1", "alice", folder_id=folder.id)
    assert len(listed) == 1

    store.update_conversation(conv.id, "t1", "alice", folder_id=None)
    assert store.get_conversation(conv.id, "t1", "alice").folder_id is None
    assert store.list_conversations("t1", "alice", unfiled_only=True)

    store.delete_folder(folder.id, "t1", "alice")
    assert store.list_folders("t1", "alice") == []


def test_tenant_isolation(tmp_path):
    store = ConversationStore(str(tmp_path / "chat.db"))
    a = store.create_conversation("t1", "alice")
    store.append_messages(a.id, "t1", "alice", [{"role": "user", "content": "secret"}])
    with pytest.raises(KeyError):
        store.get_conversation(a.id, "t1", "bob")
    with pytest.raises(KeyError):
        store.list_messages(a.id, "t2", "alice")


def test_profile_and_feedback_export(tmp_path):
    store = ConversationStore(str(tmp_path / "chat.db"))
    profile = store.upsert_profile("t1", "alice", display_name="Alice", avatar_initial="")
    assert profile.display_name == "Alice"
    assert profile.avatar_initial == "A"

    conv = store.create_conversation("t1", "alice")
    store.append_messages(
        conv.id,
        "t1",
        "alice",
        [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ],
        auto_title=False,
    )
    pairs = store.export_for_feedback(conv.id, "t1", "alice")
    assert pairs == [("Q1", "A1"), ("Q2", "A2")]
