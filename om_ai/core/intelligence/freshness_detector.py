"""Freshness detection — decide when live research is needed."""
from __future__ import annotations


class FreshnessDetector:

    SIGNALS = [
        "latest",
        "current",
        "today",
        "recent",
        "new",
        "release",
        "version",
        "price",
        "news",
        "update",
    ]

    def analyze(self, message: str) -> dict:
        """Preferred API used by brain_pipeline."""
        text = (message or "").lower()
        found = [x for x in self.SIGNALS if x in text]
        return {
            "requires_research": bool(found),
            "needs_research": bool(found),
            "requires_web": bool(found),
            "signals": found,
        }

    # Back-compat alias
    def detect(self, message: str) -> dict:
        return self.analyze(message)
