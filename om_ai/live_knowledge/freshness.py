"""Freshness routing — decide when live retrieval should run (not an LLM)."""
from __future__ import annotations

import re
from dataclasses import dataclass

_TIME_SENSITIVE = re.compile(
    r"\b("
    r"latest|current|today|tonight|yesterday|this\s+week|this\s+month|"
    r"right\s+now|as\s+of|breaking|news|release|version|changelog|"
    r"who\s+is\s+the\s+current|prime\s+minister|president|"
    r"stock\s+price|weather|score|election"
    r")\b",
    re.IGNORECASE,
)


def needs_live_knowledge(text: str) -> bool:
    return bool(_TIME_SENSITIVE.search(text or ""))


@dataclass
class FreshnessDecision:
    needs_live: bool
    reason: str
    query: str


class FreshnessRouter:
    """Route time-sensitive queries to retrieval stubs; synthesis stays OM-1.0."""

    def decide(self, messages: list[dict]) -> FreshnessDecision:
        user_bits: list[str] = []
        for m in messages:
            if str(m.get("role") or "") == "user":
                user_bits.append(str(m.get("content") or ""))
        query = "\n".join(user_bits).strip()
        if not query:
            return FreshnessDecision(False, "empty_query", "")
        if needs_live_knowledge(query):
            return FreshnessDecision(True, "time_sensitive_pattern", query)
        return FreshnessDecision(False, "static_ok", query)
