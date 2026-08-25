"""Tests for OM Agent Brain v1."""
from __future__ import annotations

from om_ai.agent import AgentBrain, ChatIntent, classify_intent
from om_ai.agent.context import pack_messages_for_tiny_context
from om_ai.agent.planner import coding_plan
from om_ai.agent.verifier import compose_fallback, verify_reply


def test_classify_intent_basic():
    assert classify_intent("hi") == ChatIntent.greeting
    assert classify_intent("who are you") == ChatIntent.identity
    assert classify_intent("fix my React Native bug") == ChatIntent.coding
    assert classify_intent("break this down into steps") == ChatIntent.agent
    assert classify_intent("what is photosynthesis") == ChatIntent.knowledge


def test_pack_messages_keeps_recent_turns():
    msgs = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "two"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "three"},
    ]
    packed = pack_messages_for_tiny_context(msgs, max_turns=1)
    assert packed[-1]["content"] == "three"
    assert len([m for m in packed if m["role"] != "system"]) <= 2


def test_agent_brain_coding_fallback():
    brain = AgentBrain()
    decision = brain.prepare(
        [{"role": "user", "content": "fix my python bug in login"}],
        tenant_id="default",
        actor="",
    )
    assert decision.intent == ChatIntent.coding
    assert decision.structured_fallback
    assert "plan" in decision.structured_fallback.lower() or "-" in decision.structured_fallback


def test_coding_plan_and_verify():
    plan = coding_plan("add login API")
    assert len(plan) >= 3
    assert verify_reply("ok") in {"too_short", "empty", ""}
    fb = compose_fallback(
        intent="coding",
        user_text="add login API",
        plan_bullets=plan,
    )
    assert "login" in fb.lower() or "plan" in fb.lower()


def test_agent_brain_passthrough_greeting():
    decision = AgentBrain().prepare([{"role": "user", "content": "hello"}])
    assert decision.intent == ChatIntent.greeting
    assert decision.meta.get("mode") == "passthrough"
