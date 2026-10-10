"""
OM RAG Ranker.
"""

from __future__ import annotations

from .rag_context import (
    RAGContext,
    RAGDocument,
)


class RAGRanker:

    def rank(
        self,
        context: RAGContext,
    ) -> RAGContext:

        ranked = sorted(
            context.documents,
            key=lambda document: (
                document.relevance,
                document.similarity,
                document.quality_score,
            ),
            reverse=True,
        )

        context.documents = ranked

        if ranked:

            context.confidence = (
                ranked[0].relevance
            )

        return context

    def filter(
        self,
        context: RAGContext,
        *,
        minimum_relevance: float = 0.30,
    ) -> RAGContext:

        context.documents = [
            document
            for document in context.documents
            if document.relevance
            >= minimum_relevance
        ]

        context.source_count = (
            len(context.documents)
        )

        context.retrieved = bool(
            context.documents
        )

        if context.documents:

            context.confidence = max(
                document.relevance
                for document in context.documents
            )

        else:

            context.confidence = 0.0

        return context