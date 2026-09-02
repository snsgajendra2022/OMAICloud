"""Classify the user ask before planning/retrieval (word-boundary safe)."""
from __future__ import annotations

import re


def is_greeting(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return bool(
        re.match(
            r"^(hi+|hello|hey+|yo|sup|namaste|नमस्ते)(\s+there)?[!?.]*$",
            t,
            re.I,
        )
    ) or (
        len(t.split()) <= 4
        and bool(re.search(r"^(hi+|hello|hey+|good\s+(morning|evening|afternoon))\b", t, re.I))
    )


def is_definitional(text: str) -> bool:
    t = (text or "").strip()
    if re.search(r"\b(create|make|build|implement|fix|debug|code)\b", t, re.I):
        return False
    return bool(
        re.search(
            r"^\s*(what|who)\s+is\b|"
            r"^\s*(explain|define)\b|"
            r"^\s*how\s+to\b|"
            r"\b(try to|want to|how do i)\s+(work|learn|use|understand|start)\b|"
            r"\bwhat\s+is\s+(git|react)\b",
            t,
            re.I,
        )
    )


def is_coding_task(text: str) -> bool:
    t = (text or "").strip()
    if is_definitional(t) or is_greeting(t):
        return False
    return bool(
        re.search(
            r"\b(create|make|build|implement|code|coding|refactor|debug)\b|"
            r"\b(react(\s+native)?|flutter|fastapi|laravel|django|vue|angular)\b|"
            r"\b(login|signup|dashboard|api)\s+(screen|page|app|project)?\b",
            t,
            re.I,
        )
    )


def is_business_task(text: str) -> bool:
    t = (text or "").strip()
    if is_coding_task(t) or is_definitional(t):
        return False
    return bool(
        re.search(r"\b(market|revenue|strategy|kpi|business|roi|go.to.market)\b", t, re.I)
    )


def query_kind(text: str) -> str:
    if is_greeting(text):
        return "greeting"
    if is_definitional(text):
        return "knowledge"
    if is_coding_task(text):
        return "coding"
    if is_business_task(text):
        return "business"
    return "general"
