"""Orchestrate dataset preparation, evaluation, and explicit training adapters."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .data.dataset_manager import DatasetManager
from .evaluation.evaluation_engine import EvaluationEngine
from .learning_config import LearningConfig


@dataclass
class LearningResult:
    status: str
    stage: str
    message: str
    dataset_version: str | None = None
    counts: dict[str, int] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningEngine:
    """Safe learning orchestrator used by CLI/API jobs and offline tests.

    Training must be supplied as an explicit adapter. No live request can
    trigger weight updates or production promotion through this class by itself.
    """

    def __init__(
        self,
        config: LearningConfig | None = None,
        dataset_manager: DatasetManager | None = None,
        evaluator: EvaluationEngine | None = None,
    ) -> None:
        self.config = config or LearningConfig.from_env()
        self.config.validate()
        self.datasets = dataset_manager or DatasetManager(self.config.root / "datasets")
        self.evaluator = evaluator or EvaluationEngine()

    def prepare(self, records: list[dict[str, Any]]) -> LearningResult:
        manifest = self.datasets.create_version(records)
        clean = self.datasets.load(manifest["dataset_version"])
        splits = self.datasets.split(
            clean,
            self.config.train_ratio,
            self.config.validation_ratio,
            self.config.test_ratio,
        )
        counts = {name: len(rows) for name, rows in splits.items()}
        return LearningResult(
            status="prepared",
            stage="dataset_versioning",
            message="Dataset validated and versioned; no model weights were changed.",
            dataset_version=manifest["dataset_version"],
            counts=counts,
            metrics={"sha256": manifest["sha256"], "schema_version": manifest["schema_version"]},
        )

    def evaluate(self, examples: list[dict[str, Any]], generate: Callable[[str], str]) -> LearningResult:
        metrics = self.evaluator.evaluate(examples, generate)
        return LearningResult(
            status="passed" if metrics["passed"] else "failed",
            stage="evaluation",
            message="Candidate response evaluation completed; production was not changed.",
            counts={"examples": metrics["count"]},
            metrics=metrics,
        )

    def train(
        self,
        dataset_version: str,
        trainer: Callable[[dict[str, list[dict[str, Any]]]], dict[str, Any]] | None = None,
    ) -> LearningResult:
        if not self.config.allow_training:
            return LearningResult(
                status="blocked",
                stage="training",
                message="Training is disabled. Set OM_LEARNING_ENABLED=true for a controlled training job.",
                dataset_version=dataset_version,
            )
        if trainer is None:
            return LearningResult(
                status="blocked",
                stage="training",
                message="No training adapter is configured; no weights were changed.",
                dataset_version=dataset_version,
            )
        records = self.datasets.load(dataset_version)
        splits = self.datasets.split(
            records,
            self.config.train_ratio,
            self.config.validation_ratio,
            self.config.test_ratio,
        )
        if not splits["train"] or not splits["validation"] or not splits["test"]:
            return LearningResult(
                status="blocked",
                stage="training",
                message="Training requires non-empty train, validation, and test splits.",
                dataset_version=dataset_version,
                counts={name: len(rows) for name, rows in splits.items()},
            )
        result = trainer(splits)
        return LearningResult(
            status="candidate",
            stage="training",
            message="Training adapter finished. Evaluate and approve its checkpoint before promotion.",
            dataset_version=dataset_version,
            counts={name: len(rows) for name, rows in splits.items()},
            metrics=result if isinstance(result, dict) else {"adapter_result": str(result)},
        )
