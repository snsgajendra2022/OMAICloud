"""Memory layer smoke tests."""
from __future__ import annotations

from om_ai.memory.short_term import ShortTermMemory
from om_ai.memory.conversation import ConversationMemory
from om_ai.memory.project_memory import ProjectMemory
from om_ai.memory.long_term import LongTermMemory


def test_short_term_memory():
    m = ShortTermMemory()
    m.remember("k", "v")
    assert m.recall("k") == "v"
    assert m.all()["k"] == "v"


def test_conversation_memory():
    c = ConversationMemory()
    c.add_user_message("hi")
    c.add_assistant_message("hello")
    ctx = c.get_context()
    assert ctx is not None


def test_project_and_long_term():
    p = ProjectMemory()
    assert isinstance(p.data, dict)
    lt = LongTermMemory()
    assert lt is not None
