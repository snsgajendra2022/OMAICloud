"""Privacy and retention policy for companion memory."""
from __future__ import annotations

import re
from typing import Any

# Structural secret patterns — not conversational keyword lists.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\b(password|passwd|pwd)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\b(bearer)\s+[a-z0-9\-_.~+/]+=*", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
    re.compile(r"\bghp_[a-zA-Z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[a-zA-Z0-9-]{10,}\b"),
)


class MemoryPolicy:
    """Decide whether content may be persisted."""

    def __init__(self, *, max_content_len: int = 8000) -> None:
        self.max_content_len = max_content_len

    def classify_sensitivity(self, content: str) -> str:
        text = (content or "").strip()
        if not text:
            return "empty"
        for pat in _SECRET_PATTERNS:
            if pat.search(text):
                return "secret"
        if len(text) > self.max_content_len:
            return "oversized"
        return "normal"

    def allow_store(self, content: str, *, kind: str = "") -> tuple[bool, str]:
        sens = self.classify_sensitivity(content)
        if sens == "secret":
            return False, "blocked_secret"
        if sens == "empty":
            return False, "empty_content"
        if sens == "oversized":
            return True, "truncated"
        if kind == "credential":
            return False, "blocked_credential_kind"
        return True, "ok"

    def sanitize_for_store(self, content: str) -> str:
        text = (content or "").strip()
        if self.classify_sensitivity(text) == "secret":
            return ""
        if len(text) > self.max_content_len:
            return text[: self.max_content_len]
        return text

    def redact_preview(self, content: str, *, max_len: int = 120) -> str:
        text = self.sanitize_for_store(content)
        if not text:
            return "[redacted]"
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def policy_summary(self) -> dict[str, Any]:
        return {
            "store_secrets": False,
            "max_content_len": self.max_content_len,
            "secret_detection": "structural_patterns",
        }
