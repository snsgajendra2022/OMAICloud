"""Consolidate working/episodic traces into semantic summaries."""
from __future__ import annotations

from typing import Any


class MemoryConsolidator:
    """Promote repeated episodic themes into semantic facts."""

    def __init__(self, *, min_repeats: int = 2) -> None:
        self.min_repeats = min_repeats

    def extract_topics(self, episodic_rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
        """Return (topic, fact) pairs worth upserting."""
        counts: dict[str, int] = {}
        last_text: dict[str, str] = {}
        for row in episodic_rows:
            content = str(row.get("content") or "").strip()
            if len(content) < 12:
                continue
            intent = str((row.get("meta") or {}).get("intent") or "")
            topic = intent or "conversation"
            counts[topic] = counts.get(topic, 0) + 1
            last_text[topic] = content[:400]
        out: list[tuple[str, str]] = []
        for topic, c in counts.items():
            if c >= self.min_repeats and topic in last_text:
                out.append((topic, f"Recent focus on {topic}: {last_text[topic][:200]}"))
        return out

    def consolidate_session(
        self,
        episodic_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        topics = self.extract_topics(episodic_rows)
        return {
            "promoted": len(topics),
            "topics": [{"topic": t, "fact": f} for t, f in topics],
        }
