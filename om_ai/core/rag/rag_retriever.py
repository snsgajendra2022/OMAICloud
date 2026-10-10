"""
OM RAG Retriever.

Retrieves relevant knowledge from the Intelligence Dataset.
"""

from __future__ import annotations

from typing import Any

from om_ai.core.intelligence_dataset import (
    DatasetManager,
)

from .rag_context import (
    RAGContext,
    RAGDocument,
)


class RAGRetriever:

    def __init__(
        self,
        dataset_manager: DatasetManager | None = None,
    ) -> None:

        self.dataset_manager = (
            dataset_manager
            or DatasetManager()
        )

    def retrieve(
        self,
        query: str,
        *,
        intent: str | None = None,
        domain: str | None = None,
        language: str | None = None,
        dataset_type: str | None = None,
        limit: int = 5,
        min_similarity: float = 0.30,
    ) -> RAGContext:

        query = (query or "").strip()

        if not query:

            return RAGContext(
                query="",
                retrieved=False,
            )

        try:

            results = (
                self.dataset_manager.semantic_search(
                    query,
                    intent=intent,
                    domain=domain,
                    language=language,
                    dataset_type=dataset_type,
                    min_similarity=min_similarity,
                    limit=limit,
                )
            )

        except Exception as exc:

            return RAGContext(
                query=query,
                retrieved=False,
                metadata={
                    "error": str(exc),
                },
            )

        documents: list[RAGDocument] = []

        for result in results or []:

            documents.append(
                RAGDocument(
                    item_id=str(
                        getattr(
                            result,
                            "item_id",
                            "",
                        )
                    ),
                    input_text=str(
                        getattr(
                            result,
                            "input_text",
                            "",
                        )
                    ),
                    ideal_response=str(
                        getattr(
                            result,
                            "ideal_response",
                            "",
                        )
                    ),
                    similarity=float(
                        getattr(
                            result,
                            "similarity",
                            0.0,
                        )
                    ),
                    domain=str(
                        getattr(
                            result,
                            "domain",
                            "",
                        )
                    ),
                    intent=str(
                        getattr(
                            result,
                            "intent",
                            "",
                        )
                    ),
                    language=str(
                        getattr(
                            result,
                            "language",
                            "",
                        )
                    ),
                    meaning=str(
                        getattr(
                            result,
                            "meaning",
                            "",
                        )
                    ),
                    reasoning_strategy=str(
                        getattr(
                            result,
                            "reasoning_strategy",
                            "",
                        )
                    ),
                    reasoning_summary=str(
                        getattr(
                            result,
                            "reasoning_summary",
                            "",
                        )
                    ),
                    verification_strategy=str(
                        getattr(
                            result,
                            "verification_strategy",
                            "",
                        )
                    ),
                    quality_score=float(
                        getattr(
                            result,
                            "quality_score",
                            0.0,
                        )
                    ),
                    source=str(
                        getattr(
                            result,
                            "source",
                            "",
                        )
                    ),
                    tags=list(
                        getattr(
                            result,
                            "tags",
                            [],
                        )
                        or []
                    ),
                    metadata=dict(
                        getattr(
                            result,
                            "metadata",
                            {},
                        )
                        or {}
                    ),
                )
            )

        confidence = (
            max(
                (
                    document.relevance
                    for document in documents
                ),
                default=0.0,
            )
        )

        return RAGContext(
            query=query,
            documents=documents,
            retrieved=bool(documents),
            confidence=confidence,
            source_count=len(documents),
            metadata={
                "intent": intent,
                "domain": domain,
                "language": language,
                "dataset_type": dataset_type,
            },
        )