"""Append-only feedback store; feedback is a candidate, never an auto-training command."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any
import uuid


class FeedbackCollector:
    def __init__(self, path: str | Path = "artifacts/learning/feedback.jsonl") -> None:
        self.path = Path(path)

    def add(
        self,
        question: str,
        answer: str,
        *,
        rating: int,
        reason: str = "",
        conversation_id: str = "",
        consent_to_training: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(rating, int) or rating not in {-1, 0, 1}:
            raise ValueError("rating must be -1 (negative), 0 (neutral), or 1 (positive).")
        if not question.strip() or not answer.strip():
            raise ValueError("question and answer must not be empty.")
        event = {
            "event_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": question.strip()[:12000],
            "answer": answer.strip()[:24000],
            "rating": rating,
            "reason": reason.strip()[:2000],
            "conversation_id": conversation_id.strip()[:200],
            "consent_to_training": bool(consent_to_training),
            "metadata": self._safe_metadata(metadata or {}),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # One append per event, with a process-local file lock supplied by the OS
        # only where available; training jobs should snapshot this file first.
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if limit <= 0 or not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
        output: list[dict[str, Any]] = []
        for line in lines[-min(limit, 1000):]:
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    output.append(row)
            except json.JSONDecodeError:
                continue
        return output

    def training_candidates(self) -> list[dict[str, Any]]:
        """Return only consented positive examples suitable for SFT.

        Negative feedback is valuable evaluation/preference signal, but the
        rejected answer must never be mislabeled as a desired training target.
        """
        return [
            {
                "question": row["question"],
                "answer": row["answer"],
                "quality_score": 1.0,
                "feedback_event_id": row["event_id"],
            }
            for row in self.recent(limit=100000)
            if row.get("consent_to_training") is True and row.get("rating") > 0
        ]

    @staticmethod
    def _safe_metadata(value: dict[str, Any]) -> dict[str, Any]:
        # Keep metadata small and JSON-safe; never store auth/token-shaped fields.
        forbidden = ("token", "secret", "password", "authorization", "api_key", "apikey")
        safe: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)[:80]
            if any(part in key_text.lower() for part in forbidden):
                continue
            try:
                encoded = json.dumps(item, ensure_ascii=False)
            except (TypeError, ValueError):
                continue
            if len(encoded) <= 1000:
                safe[key_text] = item
        return safe
