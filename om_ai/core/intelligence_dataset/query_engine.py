"""
OM Intelligence Dataset Query Engine.

Supports:

1. Structured metadata retrieval
2. Semantic retrieval
"""

from __future__ import annotations

from .dataset_item import DatasetItem
from .repository import DatasetRepository
from .semantic_retriever import SemanticRetriever


class DatasetQueryEngine:

    def __init__(
        self,
        repository: DatasetRepository | None = None,
        semantic_retriever: SemanticRetriever | None = None,
    ) -> None:

        self.repository = (
            repository
            or DatasetRepository()
        )

        self.semantic_retriever = (
            semantic_retriever
            or SemanticRetriever(
                repository=self.repository
            )
        )

    # =========================================================
    # STRUCTURED QUERY
    # =========================================================

    def find(
        self,
        *,
        intent: str | None = None,
        domain: str | None = None,
        language: str | None = None,
        dataset_type: str | None = None,
        min_quality: float = 0.0,
        limit: int = 20,
    ) -> list[DatasetItem]:

        conditions: list[str] = []

        parameters: list[object] = []

        if intent:

            conditions.append(
                "intent = ?"
            )

            parameters.append(
                intent
            )

        if domain:

            conditions.append(
                "domain = ?"
            )

            parameters.append(
                domain
            )

        if language:

            conditions.append(
                "language = ?"
            )

            parameters.append(
                language
            )

        if dataset_type:

            conditions.append(
                "dataset_type = ?"
            )

            parameters.append(
                dataset_type
            )

        conditions.append(
            "quality_score >= ?"
        )

        parameters.append(
            float(min_quality)
        )

        where = ""

        if conditions:

            where = (
                "WHERE "
                + " AND ".join(
                    conditions
                )
            )

        store = self.repository.store

        with store._connect() as connection:

            rows = connection.execute(
                f"""
                SELECT *
                FROM dataset_items
                {where}
                ORDER BY
                    quality_score DESC,
                    updated_at DESC
                LIMIT ?
                """,
                (
                    *parameters,
                    max(
                        1,
                        int(limit)
                    ),
                ),
            ).fetchall()

        return [
            store._row_to_item(row)
            for row in rows
        ]

    # =========================================================
    # SEMANTIC QUERY
    # =========================================================

    def semantic_search(
        self,
        query: str,
        *,
        intent: str | None = None,
        domain: str | None = None,
        language: str | None = None,
        dataset_type: str | None = None,
        min_quality: float = 0.0,
        min_similarity: float = 0.30,
        limit: int = 5,
    ):

        return self.semantic_retriever.search(

            query,

            intent=intent,

            domain=domain,

            language=language,

            dataset_type=dataset_type,

            min_quality=min_quality,

            min_similarity=min_similarity,

            limit=limit,
        )