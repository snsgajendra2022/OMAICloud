"""
OM RAG Context.

Represents knowledge retrieved from the OM Intelligence Dataset
before it is passed to reasoning/answer generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RAGDocument:
    item_id: str
    input_text: str
    ideal_response: str
    similarity: float = 0.0
    domain: str = ""
    intent: str = ""
    language: str = ""
    meaning: str = ""
    reasoning_strategy: str = ""
    reasoning_summary: str = ""
    verification_strategy: str = ""
    quality_score: float = 0.0
    source: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def relevance(self) -> float:
        """
        Combined retrieval relevance.

        Similarity is the primary signal.
        Dataset quality provides a secondary signal.
        """

        similarity = max(
            0.0,
            min(1.0, float(self.similarity)),
        )

        quality = max(
            0.0,
            min(1.0, float(self.quality_score)),
        )

        return round(
            similarity * 0.75
            + quality * 0.25,
            4,
        )


@dataclass(slots=True)
class RAGContext:
    query: str
    documents: list[RAGDocument] = field(
        default_factory=list
    )

    retrieved: bool = False
    confidence: float = 0.0
    source_count: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def has_knowledge(self) -> bool:
        return bool(self.documents)

    def top(self) -> RAGDocument | None:
        if not self.documents:
            return None

        return self.documents[0]

    def to_dict(self) -> dict[str, Any]:

        return {
            "query": self.query,
            "retrieved": self.retrieved,
            "confidence": self.confidence,
            "source_count": self.source_count,
            "documents": [
                {
                    "item_id": doc.item_id,
                    "input_text": doc.input_text,
                    "ideal_response": doc.ideal_response,
                    "similarity": doc.similarity,
                    "relevance": doc.relevance,
                    "domain": doc.domain,
                    "intent": doc.intent,
                    "language": doc.language,
                    "meaning": doc.meaning,
                    "reasoning_strategy": doc.reasoning_strategy,
                    "reasoning_summary": doc.reasoning_summary,
                    "verification_strategy": (
                        doc.verification_strategy
                    ),
                    "quality_score": doc.quality_score,
                    "source": doc.source,
                    "tags": doc.tags,
                }
                for doc in self.documents
            ],
            "metadata": self.metadata,
        }