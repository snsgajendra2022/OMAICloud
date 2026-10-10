from __future__ import annotations

from om_ai.core.conversation.engine import (
    ConversationEngine,
    MessageRelation,
    classify_relation,
    resolve_reference,
)


def test_answer_to_previous_question_is_not_a_new_topic():
    history = [
        {"role": "user", "content": "My React app is showing a white screen."},
        {"role": "assistant", "content": "Please check the browser console. What error do you see?"},
    ]
    assert classify_relation("I checked.", history) == MessageRelation.ANSWER


def test_short_follow_up_resolves_reference_to_prior_task():
    messages = [
        {"role": "user", "content": "The tokenizer has 340 tokens."},
        {"role": "assistant", "content": "The model checkpoint expects 65,536 tokens, so these are incompatible."},
        {"role": "user", "content": "Fix that."},
    ]
    prepared, state = ConversationEngine().prepare(messages)
    assert state.relation == MessageRelation.REFERENCE
    assert state.references
    assert "token" in state.references[0]["resolved_text"].lower()
    assert any(m["role"] == "user" and m["content"] == "Fix that." for m in prepared)
    assert any(m["role"] == "system" and "Active task/topic" in m["content"] for m in prepared)


def test_relevant_history_is_bounded_and_current_turn_is_preserved():
    messages = [{"role": "user", "content": f"Old unrelated topic {i}"} for i in range(30)]
    messages += [{"role": "assistant", "content": "We are debugging a React white screen."},
                 {"role": "user", "content": "The console says Cannot read properties of undefined."}]
    prepared, state = ConversationEngine(max_history=4, max_relevant=2).prepare(messages)
    assert prepared[-1]["content"].startswith("The console says")
    assert len([m for m in prepared if m["role"] != "system"]) <= 7
    assert state.task_status == "active"


def test_topic_switch_detected_without_phrase_response_mapping():
    history = [{"role": "user", "content": "Help debug my React white screen"},
               {"role": "assistant", "content": "Check the browser console."}]
    assert classify_relation("Compare the battery life of these two phones in 2026.", history) == MessageRelation.TOPIC_SWITCH


def test_reference_resolver_returns_grounded_prior_turn():
    history = [{"role": "user", "content": "I have a PostgreSQL duplicate rows problem."},
               {"role": "assistant", "content": "Check whether your JOIN matches multiple rows."}]
    result = resolve_reference("How do I fix that issue?", history)
    assert result is not None
    assert result["resolved_text"] in {m["content"] for m in history}
    assert 0 <= result["confidence"] <= 1
