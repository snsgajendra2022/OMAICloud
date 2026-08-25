"""Language detection / allow-list filter."""
from __future__ import annotations

from om_ai.corpus.service import _detect_language


def detect_language(text: str) -> str:
    return _detect_language(text)


def language_ok(text: str, allowed: set[str] | None = None) -> bool:
    allowed = allowed or {"en", "und"}
    return detect_language(text) in allowed
