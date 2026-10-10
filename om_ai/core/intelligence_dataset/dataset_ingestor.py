"""
OM Intelligence Dataset Ingestor.

Pipeline:

    raw record
        ↓
    normalize
        ↓
    deduplicate
        ↓
    quality score
        ↓
    DatasetItem
        ↓
    DatasetManager
        ↓
    semantic index
"""

from __future__ import annotations

from typing import Any, Iterable

from .dataset_item import DatasetItem
from .dataset_manager import DatasetManager
from .dataset_types import (
    DatasetType,
    DatasetSource,
    QualityLevel,
    LearningStatus,
)
from .deduplicator import DatasetDeduplicator
from .normalizer import DatasetNormalizer
from .quality_scorer import DatasetQualityScorer


class DatasetIngestor:

    def __init__(
        self,
        manager: DatasetManager | None = None,
        normalizer: DatasetNormalizer | None = None,
        deduplicator: DatasetDeduplicator | None = None,
        quality_scorer: DatasetQualityScorer | None = None,
    ) -> None:

        self.manager = (
            manager
            or DatasetManager()
        )

        self.normalizer = (
            normalizer
            or DatasetNormalizer()
        )

        self.deduplicator = (
            deduplicator
            or DatasetDeduplicator()
        )

        self.quality_scorer = (
            quality_scorer
            or DatasetQualityScorer()
        )

        self._seen: set[str] = set()

    # =========================================================
    # CONVERSION
    # =========================================================

    def _to_item(
        self,
        record: dict[str, Any],
    ) -> DatasetItem:

        dataset_type = DatasetType(
            record.get(
                "dataset_type",
                DatasetType.GENERAL_QA.value,
            )
        )

        source = DatasetSource(
            record.get(
                "source",
                DatasetSource.SYSTEM.value,
            )
        )

        quality = QualityLevel(
            record.get(
                "quality",
                QualityLevel.MEDIUM.value,
            )
        )

        learning_status = LearningStatus(
            record.get(
                "learning_status",
                LearningStatus.NEW.value,
            )
        )

        return DatasetItem(

            input_text=record.get(
                "input_text",
                "",
            ),

            ideal_response=record.get(
                "ideal_response",
                "",
            ),

            dataset_type=dataset_type,

            language=record.get(
                "language",
                "en",
            ),

            intent=record.get(
                "intent",
                "general",
            ),

            meaning=record.get(
                "meaning",
                "",
            ),

            goal=record.get(
                "goal",
                "",
            ),

            domain=record.get(
                "domain",
                "general",
            ),

            context=record.get(
                "context",
                {},
            ),

            reasoning_strategy=record.get(
                "reasoning_strategy",
                "",
            ),

            reasoning_summary=record.get(
                "reasoning_summary",
                "",
            ),

            expected_actions=record.get(
                "expected_actions",
                [],
            ),

            verification_strategy=record.get(
                "verification_strategy",
                "",
            ),

            source=source,

            quality=quality,

            quality_score=float(
                record.get(
                    "quality_score",
                    0.0,
                )
            ),

            learning_status=learning_status,

            tags=record.get(
                "tags",
                [],
            ),

            metadata=record.get(
                "metadata",
                {},
            ),
        )

    # =========================================================
    # ONE
    # =========================================================

    def ingest(
        self,
        record: dict[str, Any],
    ) -> DatasetItem | None:

        normalized = (
            self.normalizer.normalize(
                record
            )
        )

        if self.deduplicator.is_duplicate(
            normalized,
            self._seen,
        ):

            return None

        enriched = (
            self.quality_scorer.enrich(
                normalized
            )
        )

        item = self._to_item(
            enriched
        )

        return self.manager.add(
            item
        )

    # =========================================================
    # MANY
    # =========================================================

    def ingest_many(
        self,
        records: Iterable[
            dict[str, Any]
        ],
    ) -> dict[str, int]:

        imported = 0
        duplicates = 0
        failed = 0

        for record in records:

            try:

                result = self.ingest(
                    record
                )

                if result is None:

                    duplicates += 1

                else:

                    imported += 1

            except Exception:

                failed += 1

        return {
            "imported": imported,
            "duplicates": duplicates,
            "failed": failed,
        }