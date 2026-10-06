"""
OM Intelligence Dataset Store.

Low-level persistent storage.

SQLite is used as the default local production store so OM can
run without an external database dependency.

The storage layer knows nothing about reasoning or response generation.
It only persists validated DatasetItem records.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .dataset_item import DatasetItem


class DatasetStore:
    """Persistent SQLite storage for OM intelligence records."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        database_path: str | Path = "om_ai/data/intelligence_dataset/om_intelligence.db",
    ) -> None:

        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:

        connection = sqlite3.connect(
            str(self.database_path),
            timeout=30.0,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
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

            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS dataset_items (

                    item_id TEXT PRIMARY KEY,

                    input_text TEXT NOT NULL,

                    ideal_response TEXT NOT NULL,

                    dataset_type TEXT NOT NULL,

                    language TEXT NOT NULL,

                    intent TEXT NOT NULL,

                    meaning TEXT NOT NULL DEFAULT '',

                    goal TEXT NOT NULL DEFAULT '',

                    domain TEXT NOT NULL DEFAULT '',

                    context_json TEXT NOT NULL DEFAULT '{}',

                    reasoning_strategy TEXT NOT NULL DEFAULT '',

                    reasoning_summary TEXT NOT NULL DEFAULT '',

                    expected_actions_json TEXT NOT NULL DEFAULT '[]',

                    verification_strategy TEXT NOT NULL DEFAULT '',

                    source TEXT NOT NULL,

                    quality TEXT NOT NULL,

                    quality_score REAL NOT NULL DEFAULT 0.0,

                    learning_status TEXT NOT NULL,

                    tags_json TEXT NOT NULL DEFAULT '[]',

                    metadata_json TEXT NOT NULL DEFAULT '{}',

                    created_at TEXT NOT NULL,

                    updated_at TEXT NOT NULL,

                    schema_version INTEGER NOT NULL DEFAULT 1
                );


                CREATE INDEX IF NOT EXISTS
                idx_dataset_type
                ON dataset_items(dataset_type);


                CREATE INDEX IF NOT EXISTS
                idx_dataset_intent
                ON dataset_items(intent);


                CREATE INDEX IF NOT EXISTS
                idx_dataset_domain
                ON dataset_items(domain);


                CREATE INDEX IF NOT EXISTS
                idx_dataset_language
                ON dataset_items(language);


                CREATE INDEX IF NOT EXISTS
                idx_dataset_quality
                ON dataset_items(quality_score);


                CREATE INDEX IF NOT EXISTS
                idx_dataset_learning_status
                ON dataset_items(learning_status);


                CREATE INDEX IF NOT EXISTS
                idx_dataset_created_at
                ON dataset_items(created_at);
                """
            )

    # ---------------------------------------------------------
    # Insert / Upsert
    # ---------------------------------------------------------

    def save(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        data = item.to_dict()

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO dataset_items (
                    item_id,
                    input_text,
                    ideal_response,
                    dataset_type,
                    language,
                    intent,
                    meaning,
                    goal,
                    domain,
                    context_json,
                    reasoning_strategy,
                    reasoning_summary,
                    expected_actions_json,
                    verification_strategy,
                    source,
                    quality,
                    quality_score,
                    learning_status,
                    tags_json,
                    metadata_json,
                    created_at,
                    updated_at,
                    schema_version
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )

                ON CONFLICT(item_id)
                DO UPDATE SET

                    input_text = excluded.input_text,
                    ideal_response = excluded.ideal_response,
                    dataset_type = excluded.dataset_type,
                    language = excluded.language,
                    intent = excluded.intent,
                    meaning = excluded.meaning,
                    goal = excluded.goal,
                    domain = excluded.domain,
                    context_json = excluded.context_json,
                    reasoning_strategy = excluded.reasoning_strategy,
                    reasoning_summary = excluded.reasoning_summary,
                    expected_actions_json = excluded.expected_actions_json,
                    verification_strategy = excluded.verification_strategy,
                    source = excluded.source,
                    quality = excluded.quality,
                    quality_score = excluded.quality_score,
                    learning_status = excluded.learning_status,
                    tags_json = excluded.tags_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at,
                    schema_version = excluded.schema_version
                """,
                (
                    data["item_id"],
                    data["input_text"],
                    data["ideal_response"],
                    data["dataset_type"],
                    data["language"],
                    data["intent"],
                    data["meaning"],
                    data["goal"],
                    data["domain"],
                    json.dumps(
                        data["context"],
                        ensure_ascii=False,
                    ),
                    data["reasoning_strategy"],
                    data["reasoning_summary"],
                    json.dumps(
                        data["expected_actions"],
                        ensure_ascii=False,
                    ),
                    data["verification_strategy"],
                    data["source"],
                    data["quality"],
                    data["quality_score"],
                    data["learning_status"],
                    json.dumps(
                        data["tags"],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        data["metadata"],
                        ensure_ascii=False,
                    ),
                    data["created_at"],
                    data["updated_at"],
                    self.SCHEMA_VERSION,
                ),
            )

        return item

    # ---------------------------------------------------------
    # Get
    # ---------------------------------------------------------

    def get(
        self,
        item_id: str,
    ) -> DatasetItem | None:

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT *
                FROM dataset_items
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_item(row)

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
                DELETE FROM dataset_items
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
                SELECT COUNT(*)
                AS total
                FROM dataset_items
                """
            ).fetchone()

        return int(
            row["total"]
        )

    # ---------------------------------------------------------
    # Conversion
    # ---------------------------------------------------------

    def _row_to_item(
        self,
        row: sqlite3.Row,
    ) -> DatasetItem:

        data: dict[str, Any] = dict(row)

        data["context"] = json.loads(
            data.pop("context_json") or "{}"
        )

        data["expected_actions"] = json.loads(
            data.pop("expected_actions_json") or "[]"
        )

        data["tags"] = json.loads(
            data.pop("tags_json") or "[]"
        )

        data["metadata"] = json.loads(
            data.pop("metadata_json") or "{}"
        )

        data.pop(
            "schema_version",
            None,
        )

        return DatasetItem.from_dict(
            data
        )