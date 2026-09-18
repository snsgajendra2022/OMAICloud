"""Validate untrusted inputs at the security boundary."""
from __future__ import annotations

import re
from typing import Any

_INJECTION_MARKERS = (
    "ignore previous",
    "disregard prior",
    "system prompt",
    "you are now",
    "approve all",
    "grant permission",
    "allow everything",
)

_PATH_TRAVERSAL = re.compile(r"(^|/)\.\.(/|$)")


class InputValidator:
    def validate_user_text(self, text: str, *, max_len: int = 32_000) -> list[str]:
        errors: list[str] = []
        if not text or not text.strip():
            errors.append("empty input")
        if len(text) > max_len:
            errors.append("input too long")
        lower = text.lower()
        for marker in _INJECTION_MARKERS:
            if marker in lower:
                errors.append(f"suspicious marker: {marker}")
        return errors

    def validate_path(self, path: str) -> list[str]:
        if _PATH_TRAVERSAL.search(path.replace("\\", "/")):
            return ["path traversal"]
        return []

    def validate_action_parameters(self, params: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for key in ("authorize", "grant", "approve", "allow_everything_forever"):
            if key in params:
                errors.append(f"forbidden parameter key: {key}")
        argv = params.get("argv")
        if argv is not None and isinstance(argv, str):
            errors.append("argv must be list, not string")
        return errors
