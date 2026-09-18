"""Conversation session continuity tests."""
from om_ai.core.companion_brain.conversation_manager import ConversationManager
from om_ai.core.companion_brain.conversation_session import ConversationSession


def test_session_turn_tracking():
    session = ConversationSession(session_id="s1", actor="user")
    assert session.turn_count == 0
    session.bump_turn()
    session.bump_turn()
    assert session.turn_count == 2
    d = session.to_dict()
    assert d["session_id"] == "s1"
    assert d["interrupted"] is False


def test_manager_open_reuses_session():
    mgr = ConversationManager()
    a = mgr.open(actor="u", session_id="sess-a")
    b = mgr.open(actor="u", session_id="sess-a", project_id="om")
    assert a.session_id == b.session_id == "sess-a"
    assert b.project_id == "om"
    assert mgr.get("sess-a") is b
