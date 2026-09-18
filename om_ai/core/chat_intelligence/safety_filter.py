"""Safety filter for OM Chat Intelligence."""
from __future__ import annotations

import re
from typing import Any


class SafetyFilter:
    """Block obvious unsafe / leaked internal content from user-facing replies."""

    BLOCK_PATTERNS = [
        re.compile(r"\b(api[_-]?key|secret[_-]?key|private[_-]?key)\s*[:=]\s*\S+", re.I),
        re.compile(r"\bBEGIN (RSA |OPENSSH )?PRIVATE KEY\b"),
    ]
    INTERNAL_LEAK = re.compile(
        r"\b(system prompt|hidden chain|trace_id|OM_INTERNAL|tokenizer special)\b",
        re.I,
    )

    def filter(self, answer: str) -> dict[str, Any]:
        text = (answer or "").strip()
        flags: list[str] = []

        for pat in self.BLOCK_PATTERNS:
            if pat.search(text):
                flags.append("secret_leak")
                text = pat.sub("[redacted]", text)

        if self.INTERNAL_LEAK.search(text):
            flags.append("internal_leak")
            # Soft scrub — drop suspicious lines
            lines = []
            for line in text.splitlines():
                if self.INTERNAL_LEAK.search(line):
                    continue
                lines.append(line)
            text = "\n".join(lines).strip()

        if not text and flags:
            text = "I can help with that in a safer way — please rephrase your request."

        return {
            "answer": text,
            "flags": flags,
            "safe": "secret_leak" not in flags,
        }
