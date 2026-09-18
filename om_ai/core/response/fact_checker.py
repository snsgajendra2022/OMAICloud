"""STEP 27 — Lightweight fact / consistency checks on answers."""
from __future__ import annotations

import re
from typing import Any


class FactChecker:
    RISK = re.compile(
        r"\b(always|never|guaranteed|100%|definitely true)\b",
        re.I,
    )
    LEAK = re.compile(r"\b(api[_-]?key|secret[_-]?key|trace_id)\b", re.I)

    def check(self, answer: str, *, message: str = "") -> dict[str, Any]:
        text = (answer or "").strip()
        flags: list[str] = []
        if not text:
            flags.append("empty")
        if self.RISK.search(text):
            flags.append("overconfident")
        if self.LEAK.search(text):
            flags.append("possible_leak")
        if message and text.lower() == message.lower():
            flags.append("echo")
        ok = "empty" not in flags and "echo" not in flags and "possible_leak" not in flags
        return {
            "ok": ok,
            "flags": flags,
            "score": 0.9 if ok else (0.4 if flags else 0.7),
        }
