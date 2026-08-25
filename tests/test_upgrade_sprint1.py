"""OM Upgrade Sprint 1 — improvement loop, knowledge factory, agent runtime, quality."""
from __future__ import annotations

from om_ai.core.response.intelligence import ensure_intelligent_response
from om_ai.improvement import improve_from_exchange, run_sprint1_demo
from om_ai.improvement.evaluator import evaluate_answer


def test_improve_weak_answer_creates_dataset(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "data").mkdir()
    report = improve_from_exchange(
        "Create React login page",
        "maybe use react",
        out_dir=tmp_path / "data" / "improvements",
        bump=True,
    )
    assert report["status"] == "improved"
    assert report["weaknesses"]
    assert (tmp_path / "data" / "improvements" / "sft_improvements.jsonl").is_file()


def test_response_quality_repairs_garbage():
    out = ensure_intelligent_response(
        "Create React login page",
        "Rege — it’s Let’s a piece login maybe",
        intent="coding",
    )
    assert out["repaired"] is True
    assert "Login" in out["final"] or "login" in out["final"].lower()


def test_strong_answer_scores_high():
    from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

    md = run_reasoning_pipeline("Create React login page", retrieve=False)["markdown"]
    ev = evaluate_answer("Create React login page", md)
    assert ev["overall"] >= 70


def test_sprint1_demo_runs():
    demo = run_sprint1_demo()
    assert demo["name"] == "om-upgrade-sprint1"
    assert demo["weak_path"]["status"] == "improved"
