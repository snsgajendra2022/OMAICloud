"""Task detector — thin alias over classifier.detect_task."""
from __future__ import annotations

from typing import Any

from .classifier import detect_task


def detect(text: str) -> dict[str, Any]:
    return detect_task(text)
