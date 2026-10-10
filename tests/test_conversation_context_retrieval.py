"""Regression tests for canonical conversation context assembly."""
from __future__ import annotations

from om_ai.conversation_engine import ConversationEngine
from om_ai.conversation_engine.context_retriever import ContextRetriever


def test_current_user_turn_is_not_duplicated_in_context() -> None:
    history = [
        {"role": "user", "content": "Help me fix a React white screen."},
        {"role": "assistant", "content": "Check the browser console first."},
        {"role": "user", "content": "fix that"},
    ]
    result = ConversationEngine().process(
        "fix that",
        history=history,
        tenant_id="test-tenant",
        actor="test-user",
        conversation_id="duplicate-turn",
    )

    assert result["relation"]["relation"] == "reference_to_past"
    assert "React white screen" in result["context_blob"]
    assert result["context_blob"].count("- user: fix that") == 0


def test_confirmation_uses_last_assistant_question() -> None:
    result = ConversationEngine().process(
        "yes, please",
        history=[
            {"role": "user", "content": "The API returns a 500 error."},
            {"role": "assistant", "content": "Should I show you a safe fix?"},
            {"role": "user", "content": "yes, please"},
        ],
        tenant_id="test-tenant",
        actor="test-user",
        conversation_id="confirmation",
    )

    assert result["relation"]["relation"] == "confirmation"
    assert result["state"].last_assistant_question == "Should I show you a safe fix?"


def test_retrieved_history_preserves_chronological_order() -> None:
    retriever = ContextRetriever()
    result = retriever.retrieve(
        "React blank screen",
        [
            {"role": "user", "content": "We are building a React app."},
            {"role": "assistant", "content": "What error do you see?"},
            {"role": "user", "content": "React blank screen after login."},
        ],
        limit=3,
    )

    assert [item["role"] for item in result["history"]] == ["user", "assistant", "user"]
    assert result["history"][-1]["content"] == "React blank screen after login."


def test_memory_retrieval_failure_does_not_break_context() -> None:
    class BrokenMemory:
        def recall(self, _query: str, k: int = 6):
            raise RuntimeError("memory backend unavailable")

    result = ContextRetriever().retrieve(
        "continue the React fix",
        [{"role": "user", "content": "Fix the React login error."}],
        memory=BrokenMemory(),
    )

    assert result["history"]
    assert result["memory"] == []
