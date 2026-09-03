"""Core cognitive intelligence tests — intent-faithful answers, no echoes."""
from __future__ import annotations

from om_ai.core.intelligence import CognitiveIntelligence, run_cognitive_intelligence


def test_today_date():
    out = run_cognitive_intelligence("today date")
    u = out["understanding"]
    assert u["intent"] == "date_request"
    assert u["domain"] == "time"
    assert u["confidence"] >= 0.7
    assert "date is" in out["answer"].lower()
    assert out["answer"].strip().lower() != "today date"


def test_create_prompt_react():
    out = run_cognitive_intelligence("create prompt for react code")
    assert out["understanding"]["intent"] == "prompt_generation"
    assert out["capability"]["id"] == "prompt_generator"
    assert "prompt" in out["answer"].lower()
    assert "reusable" in out["answer"].lower() or "You are an expert" in out["answer"]
    # Must not be a full React app build dump without prompt framing
    assert out["understanding"]["action"] == "create_prompt"


def test_music_playlist():
    out = run_cognitive_intelligence("music playlist name")
    assert out["understanding"]["intent"] == "recommendation"
    assert "playlist" in out["answer"].lower() or "Deep Focus" in out["answer"]
    assert out["answer"].strip().lower() != "music playlist name"


def test_never_echo():
    ci = CognitiveIntelligence()
    for q in ["hello", "today date", "music playlist name"]:
        ans = ci.run(q)["answer"].strip().lower()
        assert ans != q.lower()
        assert not ans.startswith("understood " + q.lower())


def test_unclear_asks_clarification():
    out = run_cognitive_intelligence("xyzzy")
    # low confidence or clarify capability
    assert (
        out["understanding"].get("needs_clarification")
        or out["capability"]["id"] == "clarify"
        or "confirm" in out["answer"].lower()
        or "want me to" in out["answer"].lower()
        or out["understanding"]["confidence"] < 0.6
    )
