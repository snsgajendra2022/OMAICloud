"""Milestone-1 data pipeline + tokenizer status tests."""
from __future__ import annotations

from pathlib import Path

from om_ai.data_pipeline.cleaner import clean_text
from om_ai.data_pipeline.deduplicator import dedupe_rows
from om_ai.data_pipeline.quality_score import quality_score
from om_ai.data_pipeline.validator import ensure_layout, validate_corpus
from om_ai.data_pipeline import run_omai_corpus_v1
from om_ai.tokenizer.omai_v1 import tokenizer_v1_status
from om_ai.corpus.omai_v1 import fetch_om_owned_local
import json


def test_stage_helpers():
    assert "hello" in clean_text("  hello \n\n\n world  ")
    assert quality_score("Useful paragraph about science and learning systems. " * 4) > 0.3
    rows, removed = dedupe_rows(
        [{"text": "same"}, {"text": "same"}, {"text": "other text here enough chars"}]
    )
    assert removed == 1
    assert len(rows) == 2


def test_layout_and_pipeline(tmp_path: Path):
    root = tmp_path / "omai-corpus-v1"
    ensure_layout(root)
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
    report = run_omai_corpus_v1(root, fetch=False, tokenize=False)
    assert report["layout_validation"]["ok"] or report["layout_validation"]["has_train_txt"]
    assert (root / "sources" / "books").is_dir()
    v = validate_corpus(root)
    assert v["has_train_txt"] is True


def test_tokenizer_v1_status():
    st = tokenizer_v1_status("artifacts/tokenizer-production-65536.json")
    assert st["ok"] is True
    assert st["chat_specials_complete"] is True
