"""
OM Unified Context Document.

A normalized representation of information coming from:
- memory
- RAG
- research
- conversation
- system knowledge
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ContextDocument:

    content: str

    source_type: str

    source_id: str = ""

    relevance: float = 0.0

    confidence: float = 0.0

    importance: float = 0.0

    recency: float = 0.0

    trust: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def score(self) -> float:

        relevance = max(
            0.0,
            min(1.0, self.relevance),
        )

        confidence = max(
            0.0,
            min(1.0, self.confidence),
        )

        importance = max(
            0.0,
            min(1.0, self.importance),
        )

        recency = max(
            0.0,
            min(1.0, self.recency),
        )

        trust = max(
            0.0,
            min(1.0, self.trust),
        )

        return round(
            relevance * 0.35
            + confidence * 0.25
            + importance * 0.15
            + recency * 0.10
            + trust * 0.15,
            4,
        )

    def to_dict(self) -> dict[str, Any]:

        return {
            "content": self.content,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "relevance": self.relevance,
            "confidence": self.confidence,
            "importance": self.importance,
            "recency": self.recency,
            "trust": self.trust,
            "score": self.score(),
            "metadata": self.metadata,
        }