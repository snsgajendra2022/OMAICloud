from __future__ import annotations

from typing import Any

from .rag_context import RAGContext


class RAGQualityGate:

    def evaluate(
        self,
        context: RAGContext,
        *,
        minimum_confidence: float = 0.30,
    ) -> dict[str, Any]:

        if not context.retrieved:
            return {
                "usable": False,
                "reason": "no_retrieval",
                "confidence": 0.0,
            }

        confidence = float(
            context.confidence or 0.0
        )

        if confidence < minimum_confidence:
            return {
                "usable": False,
                "reason": "low_confidence",
                "confidence": confidence,
            }

        return {
            "usable": True,
            "reason": "relevant_knowledge_found",
            "confidence": confidence,
            "source_count": context.source_count,
        }