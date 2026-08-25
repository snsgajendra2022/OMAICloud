"""Foundation upgrade v1.0 tests."""
from __future__ import annotations

import json
from pathlib import Path

from om_ai.core.reasoning import run_reasoning_pipeline
from om_ai.knowledge.ingestion import ingest_file
from om_ai.foundation import upgrade_foundation


def test_reasoning_pipeline():
    r = run_reasoning_pipeline("Create React authentication system")
    assert r["understanding"]
    assert r["plan"]
    assert r["solution"]
    assert r["validation"]
    assert "score" in r


def test_ingest_text_file(tmp_path: Path):
    p = tmp_path / "physics_notes.txt"
    p.write_text(
        "Physics Fundamentals 1900. Mechanics energy and motion are core topics.",
        encoding="utf-8",
    )
    out = tmp_path / "corp"
    info = ingest_file(p, out_root=out)
    assert info["metadata"]["title"]
    assert info["chunk_count"] >= 1
    assert (out / "metadata").is_dir()


def test_upgrade_foundation(tmp_path: Path):
    # Run upgrade in temp root with minimal tree
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "omai-20m.json").write_text("{}", encoding="utf-8")
    # skip pytest recursion by pointing tests away — upgrade will try repo tests if present
    report = upgrade_foundation(tmp_path)
    assert report["checklist"]["Reasoning Engine"] is True
    assert (tmp_path / "artifacts" / "FOUNDATION_UPGRADE_REPORT.json").is_file()
    assert (tmp_path / "training" / "README.md").is_file()
    data = json.loads((tmp_path / "artifacts" / "FOUNDATION_UPGRADE_REPORT.json").read_text())
    assert data["name"] == "om-foundation-upgrade-v1"
