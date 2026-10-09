"""Tests for the controlled OM machine-learning lifecycle."""
from __future__ import annotations

import json

import pytest

from om_ai.core.machine_learning.data.dataset_manager import (
    DatasetManager,
    DatasetValidationError,
)
from om_ai.core.machine_learning.evaluation.evaluation_engine import EvaluationEngine
from om_ai.core.machine_learning.feedback.feedback_collector import FeedbackCollector
from om_ai.core.machine_learning.learning_config import LearningConfig
from om_ai.core.machine_learning.learning_engine import LearningEngine


def examples(count: int = 10) -> list[dict[str, str]]:
    return [
        {"question": f"Question {i}", "answer": f"Answer {i}", "intent": "general"}
        for i in range(count)
    ]


def test_dataset_versions_are_content_addressed_and_reloadable(tmp_path):
    manager = DatasetManager(tmp_path / "datasets")
    first = manager.create_version(examples())
    second = manager.create_version(examples())
    assert first["dataset_version"] == second["dataset_version"]
    assert first["sha256"] == second["sha256"]
    assert len(manager.load(first["dataset_version"])) == 10
    assert json.loads((tmp_path / "datasets" / f"{first['dataset_version']}.manifest.json").read_text())["count"] == 10


def test_dataset_validation_rejects_missing_answer(tmp_path):
    manager = DatasetManager(tmp_path)
    with pytest.raises(DatasetValidationError):
        manager.create_version([{"question": "hello"}])


def test_dataset_split_is_deterministic_and_accounts_for_every_record():
    rows = examples(11)
    first = DatasetManager.split(rows)
    second = DatasetManager.split(list(reversed(rows)))
    assert first == second
    assert sum(map(len, first.values())) == 11


def test_feedback_requires_explicit_consent_and_never_trains_on_rejected_answers(tmp_path):
    collector = FeedbackCollector(tmp_path / "feedback.jsonl")
    collector.add("q1", "a1", rating=1, consent_to_training=False)
    collector.add("q2", "rejected answer", rating=-1, consent_to_training=True)
    collector.add("q3", "preferred answer", rating=1, consent_to_training=True)
    assert len(collector.recent()) == 3
    assert collector.training_candidates() == [{
        "question": "q3",
        "answer": "preferred answer",
        "quality_score": 1.0,
        "feedback_event_id": collector.recent()[2]["event_id"],
    }]


def test_feedback_drops_secret_shaped_metadata(tmp_path):
    collector = FeedbackCollector(tmp_path / "feedback.jsonl")
    event = collector.add(
        "question", "answer", rating=1,
        metadata={"api_key": "do-not-store", "surface": "chat"},
    )
    assert "api_key" not in event["metadata"]
    assert event["metadata"]["surface"] == "chat"


def test_evaluation_detects_echo_and_empty_responses():
    evaluator = EvaluationEngine()
    result = evaluator.evaluate(
        [{"question": "What is OM?"}, {"question": "Explain memory."}],
        lambda q: "" if q.startswith("Explain") else q,
    )
    assert result["passed"] is False
    assert result["echo_rate"] == 0.5
    assert result["non_empty_rate"] == 0.5


def test_training_is_disabled_by_default(tmp_path):
    config = LearningConfig(root=tmp_path, allow_training=False)
    engine = LearningEngine(config=config)
    prepared = engine.prepare(examples(20))
    result = engine.train(prepared.dataset_version, trainer=lambda splits: {"ok": True})
    assert prepared.status == "prepared"
    assert result.status == "blocked"
    assert "no model weights" in prepared.message.lower()
