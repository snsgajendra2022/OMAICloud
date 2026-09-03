"""Retrieve relevant memory slices without topic-specific handlers."""
from __future__ import annotations

from typing import Any


class MemoryRetriever:
    def retrieve(
        self,
        question: str,
        *,
        conversation: list | None = None,
        project: Any = None,
        knowledge: Any = None,
        experience: Any = None,
        memory_context: dict | list | None = None,
    ) -> dict[str, Any]:
        hits: list[str] = []

        # Conversation snippets
        for item in (conversation or [])[-8:]:
            if isinstance(item, dict):
                text = str(item.get("content") or item.get("text") or "").strip()
            else:
                text = str(item).strip()
            if text and self._overlap(question, text) >= 0.08:
                hits.append(text[:400])

        # Generic memory_context
        if isinstance(memory_context, dict):
            relevant = memory_context.get("relevant") or memory_context.get("items") or []
            if isinstance(relevant, list):
                for r in relevant[:8]:
                    hits.append(str(r)[:400])
            elif relevant:
                hits.append(str(relevant)[:400])
        elif isinstance(memory_context, list):
            hits.extend(str(x)[:400] for x in memory_context[:8])

        if project:
            hits.append(f"project:{project}"[:400])
        if knowledge:
            if isinstance(knowledge, list):
                hits.extend(str(x)[:400] for x in knowledge[:5])
            else:
                hits.append(str(knowledge)[:400])
        if experience:
            hits.append(str(experience)[:400])

        # Deduplicate preserving order
        seen: set[str] = set()
        unique = []
        for h in hits:
            key = h.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(h)

        return {
            "items": unique[:12],
            "count": len(unique),
            "used": bool(unique),
        }

    def _overlap(self, a: str, b: str) -> float:
        ta = set((a or "").lower().split())
        tb = set((b or "").lower().split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / max(1, len(ta))
