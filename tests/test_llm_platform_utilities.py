from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.estimate_llm_memory import estimate
from scripts.validate_chat_dataset import validate


def test_70b_memory_estimate_is_not_just_weight_bytes():
    report = estimate(70_000_000_000, precision="int4", context=8192, concurrent_sequences=2)
    assert report["raw_weight_gib"] > 30
    assert report["estimated_total_gib"] > report["raw_weight_gib"]
    assert report["estimated_kv_cache_gib"] > 0


def test_memory_estimator_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        estimate(0)


def test_dataset_validator_writes_clean_manifest_data(tmp_path: Path):
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(
        json.dumps({"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]}) + "\n",
        encoding="utf-8",
    )
    report = validate(dataset)
    assert report["ok"] is True
    assert report["records_valid"] == 1
    assert len(report["source_sha256"]) == 64


def test_dataset_validator_flags_duplicates_and_eval_overlap(tmp_path: Path):
    row = {"prompt": "Question?", "completion": "Answer."}
    train = tmp_path / "train.jsonl"
    test = tmp_path / "test.jsonl"
    train.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    test.write_text(json.dumps(row) + "\n", encoding="utf-8")
    report = validate(train, test)
    assert report["exact_duplicate_records"] == 1
    assert report["eval_exact_overlap_unique_records"] == 1
    assert report["ok"] is False


def test_dataset_validator_reports_invalid_schema(tmp_path: Path):
    dataset = tmp_path / "bad.jsonl"
    dataset.write_text(json.dumps({"messages": [{"role": "user", "content": "Only user"}]}) + "\n", encoding="utf-8")
    report = validate(dataset)
    assert report["records_invalid"] == 1
    assert report["ok"] is False
