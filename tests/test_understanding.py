"""Tests for OM Cognitive Understanding Layer v1."""
from __future__ import annotations

from om_ai.understanding import understand_message
from om_ai.understanding.typo_corrector import correct_typos
from om_ai.agent import AgentBrain, ChatIntent


def test_typo_corrector_common_mistakes():
    out = correct_typos("i want complte this any how")
    assert "complete" in out.lower()
    assert "want" in out.lower()


def test_messy_understanding_example():
    raw = (
        "we ned to this best udesteing like i have mistics in mainings "
        "thne this is corrcet udesteing and thining and reply the"
    )
    u = understand_message(raw)
    assert u.confidence >= 0.85
    assert "understand" in u.understood_meaning.lower()
    assert u.intent in {"understanding_feature", "completion", "planning", "chat"}
    assert "mistake" in u.understood_meaning.lower() or "meaning" in u.understood_meaning.lower()
    assert u.public_understanding.lower().startswith("understanding:")
    assert "typo" in u.system_hint.lower() or "understood" in u.system_hint.lower()


def test_app_not_run_intent():
    u = understand_message("my app not run")
    assert u.intent == "debugging"
    assert u.needs_solution is True
    assert "not running" in u.corrected.lower() or "debug" in u.goal.lower()


def test_agent_brain_uses_understanding():
    messy = (
        "we ned to this best udesteing like i have mistics in mainings "
        "thne this is corrcet udesteing and thining and reply the"
    )
    decision = AgentBrain().prepare([{"role": "user", "content": messy}])
    assert decision.understanding is not None
    assert decision.understanding.confidence >= 0.8
    assert decision.extra_system
    assert "Understood" in decision.extra_system or "understood" in decision.extra_system.lower()
    # Should not be a bare greeting passthrough.
    assert decision.intent != ChatIntent.greeting
    assert decision.structured_fallback
    assert "Understanding:" in decision.structured_fallback
