"""Intent detection for Cognitive Understanding Layer."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class IntentResult:
    intent: str
    category: str
    needs_solution: bool
    confidence: float


_RULES: list[tuple[re.Pattern[str], str, str, bool, float]] = [
    (
        re.compile(
            r"\b(hi+|hello|hey+|namaste|नमस्ते|good\s+mor\w*|how\s+are\s+you)\b",
            re.I,
        ),
        "greeting",
        "social",
        False,
        0.95,
    ),
    (
        re.compile(r"\b(who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do)\b", re.I),
        "identity",
        "meta",
        False,
        0.92,
    ),
    (
        re.compile(
            r"\b(bug|error|crash|not\s+run|not\s+working|debug|fix|exception|stack\s*trace)\b",
            re.I,
        ),
        "debugging",
        "software",
        True,
        0.9,
    ),
    (
        re.compile(
            r"\b(slow|latency|lagging|performance)\b.*\b(site|website|app|page)\b|"
            r"\b(site|website|app|page)\b.*\b(slow|latency|lagging)\b",
            re.I,
        ),
        "performance",
        "software",
        True,
        0.9,
    ),
    (
        re.compile(
            r"\b(code|coding|implement|function|api|react|python|paython|payhthon|"
            r"typescript|sql|docker|create\s+\w*\s*code|write\s+\w*\s*code|"
            r"login\s+page|signup\s+page)\b",
            re.I,
        ),
        "coding",
        "software",
        True,
        0.88,
    ),
    (
        re.compile(
            r"\b(ui|ux|design|layout|screen|button|theme|look\s+and\s+feel)\b",
            re.I,
        ),
        "ui_design",
        "product",
        True,
        0.86,
    ),
    (
        re.compile(
            r"\b(understand|understanding|intent|meaning|typo|mistake|spelling|grammar)\b",
            re.I,
        ),
        "understanding_feature",
        "product",
        True,
        0.9,
    ),
    (
        re.compile(
            r"\b(complete|finish|100%|fully|production|ship|done)\b",
            re.I,
        ),
        "completion",
        "product",
        True,
        0.84,
    ),
    (
        re.compile(r"\b(plan|steps|roadmap|architecture|how\s+to\s+build)\b", re.I),
        "planning",
        "product",
        True,
        0.85,
    ),
    (
        re.compile(r"\b(remember|my\s+name|i\s+prefer|what\s+do\s+you\s+remember)\b", re.I),
        "memory",
        "personal",
        False,
        0.9,
    ),
    (
        re.compile(r"\b(what\s+is|explain|define|how\s+(?:do|does|to)|capital\s+of)\b", re.I),
        "knowledge",
        "qa",
        True,
        0.82,
    ),
]


def detect_intent(text: str) -> IntentResult:
    t = (text or "").strip()
    if not t:
        return IntentResult("unknown", "general", False, 0.2)
    for pat, intent, category, needs, conf in _RULES:
        if pat.search(t):
            return IntentResult(intent, category, needs, conf)
    return IntentResult("chat", "general", True, 0.55)
