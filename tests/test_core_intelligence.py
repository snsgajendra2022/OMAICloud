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
    ans = (out.get("answer") or "").strip()
    # Must NOT be the old identical reusable skeleton
    assert "Produce production-quality output" not in ans
    assert "Prefer TypeScript when building UI" not in ans
    assert "reusable" not in ans.lower() or "Prompt for:" in ans
    if ans:
        assert "react" in ans.lower() or "prompt" in ans.lower()
        from om_ai.core.intelligence.real_answer import _looks_like_garbage

        assert not _looks_like_garbage(ans)
    assert out["understanding"]["action"] == "create_prompt"


def test_music_playlist():
    out = run_cognitive_intelligence("music playlist name")
    assert out["understanding"]["intent"] == "recommendation"
    ans = (out.get("answer") or "").strip()
    if out.get("deferred") or not ans:
        assert out.get("deferred") or float((out.get("validation") or {}).get("score") or 0) < 60
    else:
        from om_ai.core.intelligence.real_answer import _looks_like_garbage

        assert not _looks_like_garbage(ans)
        assert ans.lower() != "music playlist name"


def test_never_echo():
    ci = CognitiveIntelligence()
    for q in ["hello", "today date", "music playlist name"]:
        out = ci.run(q)
        ans = (out.get("answer") or "").strip().lower()
        if not ans:
            continue
        assert ans != q.lower()
        assert not ans.startswith("understood " + q.lower())


def test_unclear_asks_clarification():
    out = run_cognitive_intelligence("xyzzy")
    assert (
        out.get("deferred")
        or out["understanding"].get("needs_clarification")
        or out["capability"]["id"] == "clarify"
        or out["understanding"]["confidence"] < 0.6
        or not (out.get("answer") or "").strip()
    )


def test_research_not_static_outline():
    out = run_cognitive_intelligence("what is recursion in programming")
    ans = (out.get("answer") or "").strip()
    assert "Here’s a clear take" not in ans
    assert "Core idea" not in ans or "```" in ans or out.get("deferred")
    assert out.get("deferred") or len(ans) > 40 or float((out.get("validation") or {}).get("score") or 0) < 60

