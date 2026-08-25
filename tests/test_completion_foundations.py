"""Completion-roadmap software foundations."""
from __future__ import annotations

import json
from pathlib import Path

from om_ai.agent.coding_agent import plan_coding_task
from om_ai.eval import run_suite
from om_ai.knowledge_universe import init_universe, universe_status
from om_ai.reasoning import reason


def test_knowledge_universe_init(tmp_path: Path):
    root = tmp_path / "uni"
    man = init_universe(root)
    assert (root / "knowledge" / "books" / "raw").is_dir()
    assert (root / "knowledge" / "code_repositories" / "embeddings").is_dir()
    assert man["paths_created"] > 0
    st = universe_status(root)
    assert st["total_raw_files"] == 0


def test_reasoning_engine():
    t = reason("Design a FastAPI auth service with JWT")
    assert t.decomposition and t.plan and t.critique
    assert "Understanding" in t.as_markdown()
    assert t.meta.get("domain") == "coding"


def test_coding_agent_plan():
    d = plan_coding_task("Add health check endpoint", root=".")
    assert d["dry_run"] is True
    assert d["steps"]
    assert d["relevant_files"] is not None


def test_eval_suite_heuristic(tmp_path: Path):
    out = tmp_path / "report.json"
    r = run_suite(report_path=out)
    assert r["total"] >= 10
    assert r["mode"] == "heuristic"
    assert r["accuracy"] >= 0.7
    assert out.is_file()
    json.loads(out.read_text(encoding="utf-8"))
