"""Solution memory — remember successful solve patterns per session/user."""
from __future__ import annotations

import threading
import time
from typing import Any


class SolutionMemory:
    """In-process memory of recent solutions (bridges to durable memory later)."""

    def __init__(self, *, max_items: int = 64) -> None:
        self.max_items = max_items
        self._lock = threading.RLock()
        self._items: list[dict[str, Any]] = []

    def recall(
        self,
        message: str,
        *,
        analysis: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        analysis = dict(analysis or {})
        ptype = str(analysis.get("problem_type") or "")
        domain = str(analysis.get("domain") or "")
        low = (message or "").lower()
        with self._lock:
            scored: list[tuple[float, dict[str, Any]]] = []
            for item in self._items:
                score = 0.0
                if ptype and item.get("problem_type") == ptype:
                    score += 0.5
                if domain and item.get("domain") == domain:
                    score += 0.3
                prev = str(item.get("message") or "").lower()
                if prev and any(w in prev for w in low.split()[:6] if len(w) > 3):
                    score += 0.2
                if score > 0:
                    scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [dict(x[1]) for x in scored[:limit]]

    def store(
        self,
        *,
        message: str,
        analysis: dict[str, Any] | None = None,
        solution: dict[str, Any] | None = None,
        confidence: float = 0.0,
    ) -> None:
        analysis = dict(analysis or {})
        solution = dict(solution or {})
        if not solution.get("solved"):
            return
        item = {
            "ts": time.time(),
            "message": (message or "")[:240],
            "problem_type": analysis.get("problem_type"),
            "domain": analysis.get("domain"),
            "kind": solution.get("kind"),
            "answer_preview": str(solution.get("answer") or "")[:280],
            "confidence": float(confidence or 0),
        }
        with self._lock:
            self._items.append(item)
            if len(self._items) > self.max_items:
                self._items = self._items[-self.max_items :]

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {"count": len(self._items), "max_items": self.max_items}
