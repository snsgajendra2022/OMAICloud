"""Rank and compress retrieved context for the model prompt."""
from __future__ import annotations

from typing import Any


class ContextIntelligence:

    def process(self, contexts: Any, query: str) -> list[Any]:
        if not contexts:
            return []

        if not isinstance(contexts, (list, tuple)):
            contexts = [contexts]

        words = set((query or "").lower().split())
        result: list[tuple[int, Any]] = []

        for item in contexts:
            if item is None or item == "":
                continue
            # Prefer summary strings over raw ResearchSource objects
            if hasattr(item, "summary_context"):
                text_src = getattr(item, "summary_context") or ""
                if text_src:
                    item = text_src
            elif hasattr(item, "content") and hasattr(item, "title"):
                item = f"{getattr(item, 'title', '')}\n{getattr(item, 'content', '')[:1500]}"

            text = str(item).lower()
            score = sum(1 for w in words if w and w in text)
            result.append((score, item))

        result.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in result[:10]]
