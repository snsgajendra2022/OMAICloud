"""Tests for production OMAI-Corpus-v1 layout + filters."""
from __future__ import annotations

import json
from pathlib import Path

from om_ai.corpus.filters import filter_document, is_toxic, quality_score
from om_ai.corpus.omai_v1 import build_omai_corpus_v1, fetch_om_owned_local


def test_filters_reject_toxic_and_score_quality():
    assert is_toxic("please kill yourself now")
    assert quality_score("This is a normal paragraph about science and learning. " * 5) > 0.35
    bad = filter_document("x")
    assert bad.ok is False
    good = filter_document(
        "Photosynthesis is how plants convert light into chemical energy for growth. " * 3
    )
    assert good.ok is True
    assert good.quality_score > 0.3


def test_production_layout_build(tmp_path: Path):
    root = tmp_path / "omai-corpus-v1"
    fetch_om_owned_local(root)
    books = root / "raw" / "books"
    books.mkdir(parents=True, exist_ok=True)
    (books / "sample.jsonl").write_text(
        json.dumps(
            {
                "source_id": "gutenberg",
                "license": "public-domain",
                "owner": "Project Gutenberg",
                "allowed_for_training": True,
                "category": "books",
                "text": "It was the best of times for learning and science. " * 30,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_omai_corpus_v1(root, fetch=False, tokenize=False)
    assert report["stages"]["license_tracking"] is True
    assert report["stages"]["toxic_content_filtering"] is True
    assert report["stages"]["train_validation_split"] is True
    assert (root / "cleaned" / "all.jsonl").is_file()
    assert (root / "deduplicated" / "all.jsonl").is_file()
    assert (root / "train" / "shard-00001.jsonl").is_file()
    assert (root / "raw" / "books").is_dir()
    assert report["pipeline_complete_pct"] >= 90.0
