"""Dynamic intelligence pipeline smoke tests."""
from __future__ import annotations

from om_ai.intelligence import IntelligenceManager, run_intelligence


def test_playlist_recommendation():
    out = run_intelligence("music playlist")
    assert out["intent"]["intent"] in {"recommend", "question", "chat"}
    assert "playlist" in out["answer"].lower() or "Deep Focus" in out["answer"]
    assert out["evaluation"]["score"] >= 70


def test_today_date_uses_clock_knowledge():
    out = run_intelligence("today date")
    assert out["understanding"]["domain"] in {"time", "general"}
    assert "date" in out["answer"].lower() or any(ch.isdigit() for ch in out["answer"])
    assert "date" in out["tools"]["tools"] or out["knowledge"]["packets"]


def test_create_prompt_react():
    out = run_intelligence("create prompt for React app")
    assert out["intent"]["intent"] in {"create_prompt", "create", "generate"}
    assert "prompt" in out["answer"].lower()
    assert "writing" in out["agents"]["team"] or "coding" in out["agents"]["primary"]


def test_quantum_explain_generalizes():
    out = run_intelligence("explain quantum computing")
    assert out["understanding"]["domain"] in {"science", "ai", "general"}
    assert len(out["answer"]) > 40
    assert out["pipeline"][0] == "understand"


def test_no_static_agent_per_topic():
    """Knowledge router uses sources, not MusicAgent/DateAgent."""
    mgr = IntelligenceManager()
    music = mgr.run("music playlist name")
    assert "MusicAgent" not in str(music)
    sources = music["knowledge"]["sources"]
    assert isinstance(sources, list) and sources
