"""Configuration for the OM AI learning lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LearningConfig:
    """Filesystem and policy settings; production promotion is opt-in."""

    root: Path = Path("artifacts/learning")
    train_ratio: float = 0.8
    validation_ratio: float = 0.1
    test_ratio: float = 0.1
    minimum_quality_score: float = 0.0
    allow_training: bool = False
    allow_auto_promotion: bool = False

    @classmethod
    def from_env(cls) -> "LearningConfig":
        root = Path(os.getenv("OM_LEARNING_ROOT", "artifacts/learning"))
        return cls(
            root=root,
            train_ratio=float(os.getenv("OM_LEARNING_TRAIN_RATIO", "0.8")),
            validation_ratio=float(os.getenv("OM_LEARNING_VALIDATION_RATIO", "0.1")),
            test_ratio=float(os.getenv("OM_LEARNING_TEST_RATIO", "0.1")),
            minimum_quality_score=float(os.getenv("OM_LEARNING_MIN_QUALITY", "0")),
            allow_training=_env_bool("OM_LEARNING_ENABLED", False),
            # Always default off; enabling requires an explicit deployment choice.
            allow_auto_promotion=_env_bool("OM_LEARNING_AUTO_PROMOTION", False),
        )

    def validate(self) -> None:
        ratios = (self.train_ratio, self.validation_ratio, self.test_ratio)
        if any(r < 0 or r > 1 for r in ratios):
            raise ValueError("Dataset split ratios must be between 0 and 1.")
        if abs(sum(ratios) - 1.0) > 1e-8:
            raise ValueError("Dataset split ratios must add up to 1.")
        if not 0 <= self.minimum_quality_score <= 1:
            raise ValueError("minimum_quality_score must be between 0 and 1.")
