"""
Public reply sanitizer — never leak internals to the user.

Strips: Knowledge Brain, Memory dumps, Connected systems, tool chrome,
file paths, workflow/decision JSON, Genesis training templates, research dumps.
"""
from __future__ import annotations

import re


_INTERNAL_HEADERS = re.compile(
    r"(?im)^\s*##\s*("
    r"Knowledge Brain|Cross-lingual knowledge|Memory|Connected systems|"
    r"Tool results|Internal context|Research notes"
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

_EVALUATOR_CHROME = re.compile(
    r"(?im)^\s*("
    r"Address the user ask directly:.*|"
    r"Requirements from evaluator.*|"
    r"##\s*Requirements from evaluator.*|"
    r"##\s*Understanding.*|"
    r"Understanding|"
    r"Write shorter clear sentences.*|"
    r"avoid garbled fragments.*|"
    r"Address every part of the user ask explicitly.*|"
    r"Include runnable code blocks and tests.*|"
    r"Use clear sections:.*|"
    r"Question:\s*.*|"
    r"[a-zA-Z0-9_\-.]+\.jsonl?"
    r")\s*$"
)

_FILE_PATH = re.compile(
    r"(?i)(?:^|\s)(?:/Users/[^\s]+|/home/[^\s]+|[A-Z]:\\[^\s]+|"
    r"om_ai/[^\s,]+\.py|artifacts/[^\s]+)"
)

_DICT_DUMP = re.compile(
    r"\{['\"]?(?:goal|selected|scores|risk|strategy|id|title|agent|plan|analysis|validation|result)['\"]?\s*:"
)

_GENESIS_BAD = re.compile(
    r"(?is)belongs in the OM Genesis knowledge map|"
    r"Variant focus:|"
    r"Map this to OM AI modules first|"
    r"Teach OM-1\.0 about|"
    r"Genesis-JARVIS|"
    r"bio-digital ideas labeled as research"
)


def looks_like_genesis_template(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if _GENESIS_BAD.search(t):
        return True
    low = t.lower()
    if "## topic" in low and "## explanation" in low and (
        "## horizon" in low or "practical next step" in low
    ):
        return True
    return False


def extract_clean_tool_answer(tool_blob: str) -> str:
    """Keep only useful tool output (date/calc/facts), drop chrome + genesis junk."""
    if not tool_blob:
        return ""
    text = tool_blob.strip()
    if looks_like_genesis_template(text):
        return ""

    m = re.search(r"Today's date is[^\n.]+\.?", text, re.I)
    if m and "##" not in text[: m.start()]:
        if "[tool:date]" in text.lower() or "today's date" in text.lower():
            return m.group(0).strip()

    m = re.search(r"(\d+(?:\.\d+)?%\s*of\s*\d+(?:\.\d+)?\s*=\s*\d+(?:\.\d+)?)", text)
    if m:
        return m.group(1).strip()

    cleaned = sanitize_public_reply(text)
    if looks_like_genesis_template(cleaned):
        return ""
    if cleaned and len(cleaned) < 1200 and not _looks_internal(cleaned):
        # Prefer factual tool answers (React fact table etc.)
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
        "om genesis knowledge map",
        "research notes:",
        "**research notes:**",
    )
    return any(m in low for m in markers) or looks_like_genesis_template(text)


def sanitize_public_reply(text: str) -> str:
    """Remove internal pipeline sections from user-visible answers."""
    if not text:
        return ""
    if looks_like_genesis_template(text):
        return ""

    # Drop Research notes dumps entirely
    text = re.split(r"(?im)\n\s*\*{0,2}Research notes:\*{0,2}\s*\n", text, maxsplit=1)[0]

    lines = (text or "").splitlines()
    out: list[str] = []
    skip_section = False
    for line in lines:
        if _INTERNAL_HEADERS.match(line):
            skip_section = True
            continue
        if skip_section:
            if re.match(r"(?im)^\s*##\s+\S+", line) and not _INTERNAL_HEADERS.match(line):
                skip_section = False
            else:
                continue
        if _INTERNAL_LINE.match(line):
            continue
        if _EVALUATOR_CHROME.match(line):
            continue
        if _DICT_DUMP.search(line):
            continue
        if _FILE_PATH.search(line) and len(line.strip()) < 200:
            continue
        out.append(line)

    cleaned = "\n".join(out).strip()
    cleaned = re.sub(r"\[tool:[^\]]+\]\s*", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*##\s*Tool results\s*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if looks_like_genesis_template(cleaned) or _looks_internal(cleaned) or not cleaned:
        return ""
    return cleaned


def is_safe_public_answer(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if looks_like_genesis_template(t):
        return False
    if _looks_internal(t):
        return False
    if "## Knowledge" in t or "[layered]" in t or "[decision]" in t:
        return False
    if "[tool:" in t.lower():
        return False
    return True
