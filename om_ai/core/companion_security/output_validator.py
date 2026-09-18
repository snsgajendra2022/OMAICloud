"""Validate outputs before returning to users or logs."""
from __future__ import annotations

from typing import Any

from .secret_filter import redact_text, redact_value


class OutputValidator:
    def sanitize_for_log(self, payload: Any) -> Any:
        return redact_value(payload)

    def sanitize_for_user(self, text: str, *, max_len: int = 100_000) -> str:
        cleaned = redact_text(text)
        if len(cleaned) > max_len:
            return cleaned[:max_len] + "\n…[truncated]"
        return cleaned

    def validate_no_raw_secrets(self, text: str) -> list[str]:
        redacted = redact_text(text)
        if redacted != text:
            return ["output contained sensitive patterns"]
        return []
