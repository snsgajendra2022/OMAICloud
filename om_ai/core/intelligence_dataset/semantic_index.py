"""
OM Semantic Dataset Index.

Persistent vector storage built on SQLite.

This provides:

    DatasetItem
        +
    Embedding
        =
    Semantic Retrieval Index
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Sequence


class SemanticIndex:

    SCHEMA_VERSION = 1

    def __init__(
        self,
        database_path: str | Path = (
            "om_ai/data/intelligence_dataset/"
            "om_intelligence.db"
        ),
    ) -> None:

        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def _connect(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            str(self.database_path),
            timeout=30.0,
        )

        connection.row_factory = (
            sqlite3.Row
        )

        connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        connection.execute(
            "PRAGMA synchronous = NORMAL"
        )

        return connection

    # ---------------------------------------------------------
    # Schema
    # ---------------------------------------------------------

    def _initialize(self) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                dataset_embeddings (

                    item_id TEXT PRIMARY KEY,

                    embedding_json TEXT NOT NULL,

                    dimension INTEGER NOT NULL,

                    model_name TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    updated_at TEXT NOT NULL,

                    schema_version INTEGER NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_embedding_model

                ON dataset_embeddings(model_name)
                """
            )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    def save(
        self,
        item_id: str,
        embedding: Sequence[float],
        model_name: str,
        timestamp: str,
    ) -> None:

        vector = [
            float(value)
            for value in embedding
        ]

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO dataset_embeddings (

                    item_id,
                    embedding_json,
                    dimension,
                    model_name,
                    created_at,
                    updated_at,
                    schema_version

                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(item_id)
                DO UPDATE SET

                    embedding_json =
                        excluded.embedding_json,

                    dimension =
                        excluded.dimension,

                    model_name =
                        excluded.model_name,

                    updated_at =
                        excluded.updated_at,

                    schema_version =
                        excluded.schema_version
                """,
                (
                    item_id,
                    json.dumps(
                        vector
                    ),
                    len(vector),
                    model_name,
                    timestamp,
                    timestamp,
                    self.SCHEMA_VERSION,
                ),
            )

    # ---------------------------------------------------------
    # Get
    # ---------------------------------------------------------

    def get(
        self,
        item_id: str,
    ) -> list[float] | None:

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT embedding_json
                FROM dataset_embeddings
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()

        if row is None:

            return None

        return [
            float(value)
            for value in json.loads(
                row["embedding_json"]
            )
        ]

    # ---------------------------------------------------------
    # All
    # ---------------------------------------------------------

    def all(
        self,
    ) -> list[tuple[str, list[float], str]]:

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    item_id,
                    embedding_json,
                    model_name

                FROM dataset_embeddings
                """
            ).fetchall()

        return [

            (
                row["item_id"],

                [
                    float(value)
                    for value in json.loads(
                        row["embedding_json"]
                    )
                ],

                row["model_name"],
            )

            for row in rows
        ]

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(
        self,
        item_id: str,
    ) -> bool:

        with self._connect() as connection:

            cursor = connection.execute(
                """
                DELETE FROM dataset_embeddings
                WHERE item_id = ?
                """,
                (item_id,),
            )

            return cursor.rowcount > 0

    # ---------------------------------------------------------
    # Count
    # ---------------------------------------------------------

    def count(self) -> int:

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM dataset_embeddings
                """
            ).fetchone()

        return int(
            row["total"]
        )