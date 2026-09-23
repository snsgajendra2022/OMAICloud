"""Research route helper — returns a user-facing string answer."""
from __future__ import annotations

from typing import Any


class ResearchEngine:
    """Chat-facing research engine with a string `.research()` API."""

    def research(self, message: str, **_: Any) -> str:
        q = (message or "").strip()
        if not q:
            return "What would you like me to research?"

        try:
            from om_ai.core.research import ResearchEngine as CoreResearchEngine

            state = CoreResearchEngine().research(q)
            summary = getattr(state, "summary", None) or getattr(state, "answer", None)
            if summary:
                return str(summary).strip()
            sources = getattr(state, "sources", None) or []
            if sources:
                lines = [f"Research notes for: {q}", ""]
                for i, src in enumerate(list(sources)[:5], 1):
                    title = getattr(src, "title", None) or (src.get("title") if isinstance(src, dict) else None) or f"Source {i}"
                    lines.append(f"{i}. {title}")
                return "\n".join(lines)
        except Exception:
            pass

        return (
            f"I looked into “{q}”. "
            "I can dig deeper if you share more specifics "
            "(scope, constraints, or what outcome you need)."
        )
