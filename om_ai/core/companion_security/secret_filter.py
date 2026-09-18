"""Redact secrets before logging or export."""
from __future__ import annotations

import re
from typing import Any

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|authorization)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-_.~+/]+=*"),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
)

_REDACTED = "[REDACTED]"


def redact_text(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub(_REDACTED, out)
    return out


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {k: redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(redact_value(v) for v in value)
    return value
