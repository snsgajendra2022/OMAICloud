"""Human-facing context assembly for companion turns."""
from __future__ import annotations

from typing import Any


class HumanContext:
    def build(
        self,
        *,
        message: str,
        history: list[dict[str, Any]] | None,
        memory_blob: str = "",
        preferences: dict[str, str] | None = None,
        relationship: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hist = list(history or [])
        followup = len(hist) > 0 and len((message or "").split()) < 14
        parts: list[str] = []
        if memory_blob:
            parts.append(f"Memory:\n{memory_blob}")
        if preferences:
            pref_line = ", ".join(f"{k}={v}" for k, v in preferences.items())
            parts.append(f"Preferences: {pref_line}")
        if relationship:
            parts.append(
                f"Relationship: {relationship.get('depth', 'new')} "
                f"(familiarity {relationship.get('familiarity', 0)})"
            )
        if extra:
            for k, v in extra.items():
                if v is not None and str(v).strip():
                    parts.append(f"{k}: {str(v)[:300]}")
        return {
            "followup": followup,
            "history_count": len(hist),
            "context_blob": "\n".join(parts).strip()[:2500],
            "history": hist,
        }
