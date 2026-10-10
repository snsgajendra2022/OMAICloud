from om_ai.core.chat_intelligence.conversation_memory import ConversationMemory


def test_memory_is_isolated_by_tenant_and_actor():
    memory = ConversationMemory()
    a = memory.session_id("tenant-a", "user-1")
    b = memory.session_id("tenant-b", "user-1")
    c = memory.session_id("tenant-a", "user-2")

    memory.add(a, "user", "private context A")
    memory.add(b, "user", "private context B")
    memory.add(c, "user", "private context C")

    assert "private context A" in [row["content"] for row in memory.history(a)]
    assert "private context A" not in [row["content"] for row in memory.history(b)]
    assert "private context A" not in [row["content"] for row in memory.history(c)]


def test_memory_clear_removes_only_the_selected_session():
    memory = ConversationMemory()
    a = memory.session_id("tenant", "alice")
    b = memory.session_id("tenant", "bob")
    memory.add(a, "user", "Alice context")
    memory.add(b, "user", "Bob context")

    memory.clear(a)

    assert memory.history(a) == []
    assert [row["content"] for row in memory.history(b)] == ["Bob context"]


def test_memory_bounds_stored_content_and_history():
    memory = ConversationMemory(max_turns=2)
    session = memory.session_id("tenant", "user")
    memory.add(session, "user", "x" * 5000)
    memory.add(session, "assistant", "first")
    memory.add(session, "user", "last")

    rows = memory.history(session)
    assert len(rows) == 2
    assert all(len(row["content"]) <= 4000 for row in rows)
    assert rows[-1]["content"] == "last"
