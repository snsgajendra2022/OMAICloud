"""
OM Intelligence Dataset Item.

Represents one high-quality learning/evaluation example.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .dataset_types import (
    DatasetSource,
    DatasetType,
    LearningStatus,
    QualityLevel,
)


@dataclass(slots=True)
class DatasetItem:
    """
    One complete OM intelligence example.

    The dataset intentionally stores more than:

        question -> answer

    because OM needs:

        input
        meaning
        intent
        context
        reasoning strategy
        answer
        verification
        quality
    """

    input_text: str

    ideal_response: str

    dataset_type: DatasetType = DatasetType.GENERAL_QA

    language: str = "en"

    intent: str = "general"

    meaning: str = ""

    goal: str = ""

    domain: str = ""

    context: dict[str, Any] = field(
        default_factory=dict
    )

    reasoning_strategy: str = ""

    reasoning_summary: str = ""

    expected_actions: list[str] = field(
        default_factory=list
    )

    verification_strategy: str = ""

    source: DatasetSource = DatasetSource.SYSTEM

    quality: QualityLevel = QualityLevel.UNKNOWN

    quality_score: float = 0.0

    learning_status: LearningStatus = LearningStatus.NEW

    tags: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    item_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )

    updated_at: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )


    def to_dict(self) -> dict[str, Any]:

        return {
            "item_id": self.item_id,
            "input_text": self.input_text,
            "ideal_response": self.ideal_response,
            "dataset_type": self.dataset_type.value,
            "language": self.language,
            "intent": self.intent,
            "meaning": self.meaning,
            "goal": self.goal,
            "domain": self.domain,
            "context": self.context,
            "reasoning_strategy": self.reasoning_strategy,
            "reasoning_summary": self.reasoning_summary,
            "expected_actions": self.expected_actions,
            "verification_strategy": self.verification_strategy,
            "source": self.source.value,
            "quality": self.quality.value,
            "quality_score": self.quality_score,
            "learning_status": self.learning_status.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "DatasetItem":

        return cls(

            item_id=str(
                data.get("item_id")
                or uuid4()
            ),

            input_text=str(
                data.get("input_text")
                or ""
            ),

            ideal_response=str(
                data.get("ideal_response")
                or ""
            ),

            dataset_type=DatasetType(
                data.get(
                    "dataset_type",
                    DatasetType.GENERAL_QA.value,
                )
            ),

            language=str(
                data.get("language")
                or "en"
            ),

            intent=str(
                data.get("intent")
                or "general"
            ),

            meaning=str(
                data.get("meaning")
                or ""
            ),

            goal=str(
                data.get("goal")
                or ""
            ),

            domain=str(
                data.get("domain")
                or ""
            ),

            context=dict(
                data.get("context")
                or {}
            ),

            reasoning_strategy=str(
                data.get("reasoning_strategy")
                or ""
            ),

            reasoning_summary=str(
                data.get("reasoning_summary")
                or ""
            ),

            expected_actions=list(
                data.get("expected_actions")
                or []
            ),

            verification_strategy=str(
                data.get("verification_strategy")
                or ""
            ),

            source=DatasetSource(
                data.get(
                    "source",
                    DatasetSource.SYSTEM.value,
                )
            ),

            quality=QualityLevel(
                data.get(
                    "quality",
                    QualityLevel.UNKNOWN.value,
                )
            ),

            quality_score=float(
                data.get("quality_score")
                or 0.0
            ),

            learning_status=LearningStatus(
                data.get(
                    "learning_status",
                    LearningStatus.NEW.value,
                )
            ),

            tags=list(
                data.get("tags")
                or []
            ),

            metadata=dict(
                data.get("metadata")
                or {}
            ),

            created_at=str(
                data.get("created_at")
                or datetime.now(
                    timezone.utc
                ).isoformat()
            ),

            updated_at=str(
                data.get("updated_at")
                or datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        )