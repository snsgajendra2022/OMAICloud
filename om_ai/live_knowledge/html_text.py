"""Deterministic HTML → plain text (no LLM)."""
from __future__ import annotations

import re
from html import unescape

_SCRIPT_STYLE = re.compile(
    r"<(script|style|noscript|svg|iframe)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\f\r]+")
_BLANK = re.compile(r"\n{3,}")


def html_to_text(html: str, *, max_chars: int = 6000) -> str:
    """Strip tags/scripts and collapse whitespace."""
    if not html:
        return ""
    text = _SCRIPT_STYLE.sub(" ", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"(?i)</(div|h[1-6]|li|tr)>", "\n", text)
    text = _TAG.sub(" ", text)
    text = unescape(text)
    text = _WS.sub(" ", text)
    text = _BLANK.sub("\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text[:max_chars].strip()


def extract_title(html: str) -> str:
    if not html:
        return ""
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if not m:
        return ""
    return _TAG.sub("", unescape(m.group(1))).strip()[:200]
