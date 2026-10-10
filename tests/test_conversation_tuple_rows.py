"""Regression tests for SQLite conversation row handling."""
from __future__ import annotations

import sqlite3

from om_ai.memory.conversations import ConversationStore


def test_list_conversations_handles_tuple_rows(tmp_path):
    store = ConversationStore(str(tmp_path / "conversations.sqlite3"))
    try:
        created = store.create_conversation(
            "tenant-test", "user:test-user", title="New chat"
        )
        store.append_messages(
            created.id,
            "tenant-test",
            "user:test-user",
            [{"role": "user", "content": "Hello OM"}],
        )

        # Simulate a connection whose row_factory has been reset by another
        # integration. SQLite then returns tuples instead of sqlite3.Row.
        store._conn.row_factory = None

        chats = store.list_conversations("tenant-test", "user:test-user")
        assert len(chats) == 1
        assert chats[0].id == created.id
        assert chats[0].title == "Hello OM"
        assert chats[0].message_count == 1
    finally:
        store.close()
