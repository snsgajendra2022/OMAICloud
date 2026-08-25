"""Tests for OM Knowledge Brain corpus."""
from __future__ import annotations

import json
from pathlib import Path

from om_ai.knowledge_brain import init_corpus, knowledge_catalog, write_instruct_dataset
from om_ai.training.sft import _row_to_messages


def test_catalog_has_eras_and_domains():
    cat = knowledge_catalog()
    assert cat["coverage"] == "1600–2026"
    assert len(cat["eras"]) == 7
    assert len(cat["domains"]) >= 10
    assert "2026" in cat["system"]
    assert "Genesis Universal" in cat["system"]


def test_init_and_generate(tmp_path: Path):
    root = tmp_path / "kb"
    man = init_corpus(root)
    assert (root / "manifest.json").is_file()
    assert (root / "knowledge" / "mathematics" / "raw").is_dir()
    assert (root / "eras" / "era7_generative_ai" / "era.json").is_file()
    assert man["coverage"] == "1600–2026"

    out = root / "train" / "kb.jsonl"
    built = write_instruct_dataset(out, count=40, also_init_corpus=False, root=root)
    assert built["count"] == 40
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    msgs, resp = _row_to_messages(row)
    assert msgs and resp
    assert "Understanding" in resp or "Analysis" in resp


def test_generate_scales_past_old_cap(tmp_path: Path):
    """Generator must exceed the old ~3k unique template ceiling."""
    out = tmp_path / "big.jsonl"
    built = write_instruct_dataset(out, count=5000, also_init_corpus=True, root=tmp_path / "kb")
    assert built["count"] == 5000
    assert "Genesis Universal" in built["system"]
