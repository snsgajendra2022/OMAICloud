"""
Public reply sanitizer — never leak internals to the user.

Strips: Knowledge Brain, Memory dumps, Connected systems, tool chrome,
file paths, workflow/decision JSON, layered memory traces.
"""
from __future__ import annotations

import re


_INTERNAL_HEADERS = re.compile(
    r"(?im)^\s*##\s*("
    r"Knowledge Brain|Cross-lingual knowledge|Memory|Connected systems|"
    r"Tool results|Internal context"
    r")\s*$"
)

_INTERNAL_LINE = re.compile(
    r"(?im)^\s*("
    r"\[tool:[^\]]+\]|"
    r"\[layered\]|"
    r"\[workflow\]|"
    r"\[decision\]|"
    r"\[personal\]|"
    r"\[experience\]|"
    r"\[preference\]|"
    r"\[text\]|"
    r"\[image\]|"
    r"\[pdf\]|"
    r"\[code_intelligence\]|"
    r"\[knowledge_graph\]"
    r").*$"
)

_FILE_PATH = re.compile(
    r"(?i)(?:^|\s)(?:/Users/[^\s]+|/home/[^\s]+|[A-Z]:\\[^\s]+|"
    r"om_ai/[^\s,]+\.py|artifacts/[^\s]+)"
)

_DICT_DUMP = re.compile(r"\{['\"]?(?:goal|selected|scores|risk|strategy|id|title|agent)['\"]?\s*:")


def extract_clean_tool_answer(tool_blob: str) -> str:
    """Keep only useful tool output (date/calc), drop chrome."""
    if not tool_blob:
        return ""
    text = tool_blob.strip()
    # Date line
    m = re.search(
        r"Today's date is[^\n.]+\.?",
        text,
        re.I,
    )
    if m and "##" not in text[: m.start()]:
        # Prefer date-only if this looks like a date tool reply
        if "[tool:date]" in text.lower() or "today's date" in text.lower():
            return m.group(0).strip()
    # Calculator
    m = re.search(r"(\d+(?:\.\d+)?%\s*of\s*\d+(?:\.\d+)?\s*=\s*\d+(?:\.\d+)?)", text)
    if m:
        return m.group(1).strip()
    # Strip known headers and return first clean paragraph if short tool result
    cleaned = sanitize_public_reply(text)
    if cleaned and len(cleaned) < 280 and not _looks_internal(cleaned):
        return cleaned
    return ""


def _looks_internal(text: str) -> bool:
    low = (text or "").lower()
    markers = (
        "knowledge brain",
        "cross-lingual",
        "[layered]",
        "[workflow]",
        "[decision]",
        "connected systems",
        "om ai foundation sample",
        "physics mechanics energy",
    )
    return any(m in low for m in markers)


def sanitize_public_reply(text: str) -> str:
    """Remove internal pipeline sections from user-visible answers."""
    if not text:
        return ""
    lines = (text or "").splitlines()
    out: list[str] = []
    skip_section = False
    for line in lines:
        if _INTERNAL_HEADERS.match(line):
            skip_section = True
            continue
        if skip_section:
            # New markdown header ends the skipped section
            if re.match(r"(?im)^\s*##\s+\S+", line) and not _INTERNAL_HEADERS.match(line):
                skip_section = False
            else:
                continue
        if _INTERNAL_LINE.match(line):
            continue
        if _DICT_DUMP.search(line):
            continue
        # Drop lines that are mostly file paths
        if _FILE_PATH.search(line) and len(line.strip()) < 200:
            continue
        out.append(line)

    cleaned = "\n".join(out).strip()
    # Remove leftover tool tags inline
    cleaned = re.sub(r"\[tool:[^\]]+\]\s*", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*##\s*Tool results\s*$", "", cleaned)
    # Collapse blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if _looks_internal(cleaned) or not cleaned:
        return ""
    return cleaned


def is_safe_public_answer(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if _looks_internal(t):
        return False
    if "## Knowledge" in t or "[layered]" in t or "[decision]" in t:
        return False
    return True
