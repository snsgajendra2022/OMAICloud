"""Intelligence upgrades: reasoning quality, garble gate, learning cycle, document AI."""
from __future__ import annotations

from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
from om_ai.learning import quality_check_reply, record_feedback, run_learning_cycle
from om_ai.multimodal.document_ai import multimodal_status
from om_ai.runtime.chat_orchestrator import is_garbled_generation, is_low_quality_reply


def test_reasoning_react_login_has_code():
    r = run_reasoning_pipeline("Create React login page", retrieve=False)
    md = r["markdown"]
    assert "## Understanding" in md
    assert "## Architecture" in md
    assert "Login.jsx" in md
    assert "validate" in md.lower() or "validation" in md.lower()


def test_reasoning_school_management():
    r = run_reasoning_pipeline("Design a school management system", retrieve=False)
    md = r["markdown"]
    assert "Architecture" in md
    assert "Students" in md or "students" in r["solution"].lower()


def test_garbled_quality_gate():
    junk = (
        "👋 ाम that at Prime Minister sentence... syntax! ही म clear clear there. "
        "ठ (formal) वg Dail name so well — good powered byHi!"
    )
    assert is_garbled_generation(junk)
    assert is_low_quality_reply(junk) == "garbled"
    assert quality_check_reply(junk, user_ask="hi")["ok"] is False


def test_learning_feedback_queue(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()
    r = record_feedback(
        problem="2+2",
        old_answer="wrong",
        correct_answer="4",
        rating=1,
        db=str(tmp_path / "artifacts" / "feedback.sqlite3"),
    )
    assert r["stored"] and r["improvement_queue_updated"]
    cycle = run_learning_cycle(out_dir=tmp_path / "continuous", weak_areas=["math"])
    assert cycle["status"] == "ok"
    assert (tmp_path / "continuous" / "recipe.json").is_file()


def test_multimodal_status_document_ready():
    st = multimodal_status()
    assert st["document"] == "ready"
