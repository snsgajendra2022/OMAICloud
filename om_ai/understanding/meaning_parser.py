"""Parse clarified meaning / user goal from messy chat text."""
from __future__ import annotations

import re
from dataclasses import dataclass

from om_ai.understanding.intent_detector import IntentResult
from om_ai.understanding.typo_corrector import correct_typos


@dataclass(slots=True)
class MeaningResult:
    original: str
    corrected: str
    understood_meaning: str
    goal: str
    confidence: float


_GOAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"understand.*(mistake|meaning|typo|incorrect|wrong).*reply|"
            r"(mistake|typo).*(understand|thinking|reply)",
            re.I,
        ),
        "Make OM understand messy messages, then think and reply correctly.",
    ),
    (
        re.compile(r"(complete|finish).*(fully|anyway|anyhow|100)|any\s*how", re.I),
        "Complete the task fully end-to-end.",
    ),
    (
        re.compile(r"(best\s+)?ui|improve.*(design|look|screen)", re.I),
        "Improve UI quality with practical design and implementation help.",
    ),
    (
        re.compile(r"(app|server|build).*(not\s+run|crash|error|bug)|fix.*(bug|error)", re.I),
        "Debug and fix the software issue.",
    ),
    (
        re.compile(r"\b(plan|roadmap|architecture|how\s+to\s+build)\b", re.I),
        "Get a clear implementation plan / architecture.",
    ),
]


def parse_meaning(original: str, *, intent: IntentResult | None = None) -> MeaningResult:
    raw = (original or "").strip()
    corrected = correct_typos(raw)
    intent = intent or IntentResult("chat", "general", True, 0.5)

    goal = "Help with the user's request."
    for pat, g in _GOAL_PATTERNS:
        if pat.search(corrected) or pat.search(raw):
            goal = g
            break
    if intent.intent == "understanding_feature":
        goal = (
            "Add / improve OM's ability to understand incorrect messages, "
            "detect intent, think, and reply correctly."
        )
    elif intent.intent == "debugging":
        goal = "Diagnose the failure and provide a practical fix."
    elif intent.intent == "ui_design":
        goal = "Improve UI quality with concrete suggestions."
    elif intent.intent == "coding":
        goal = "Help implement or improve the code."
    elif intent.intent == "completion":
        goal = "Complete the remaining work fully."

    # Build a short human-readable paraphrase.
    if intent.intent == "understanding_feature":
        understood = (
            "User wants OM AI to understand messages even when there are "
            "mistakes in spelling and meaning, then correctly understand, "
            "think, and reply."
        )
        conf = max(0.9, intent.confidence)
    elif corrected.lower() != raw.lower() and len(corrected.split()) >= 4:
        understood = f"User means: {corrected}"
        conf = min(0.95, 0.7 + 0.05 * abs(len(raw) - len(corrected)))
    elif intent.intent == "greeting":
        understood = "User is greeting OM."
        conf = 0.95
    else:
        understood = f"User is asking about: {corrected or raw}"
        conf = intent.confidence

    # Confidence penalty if message is extremely short / empty.
    if len((corrected or raw).split()) <= 1:
        conf = min(conf, 0.5)

    return MeaningResult(
        original=raw,
        corrected=corrected or raw,
        understood_meaning=understood,
        goal=goal,
        confidence=round(conf, 2),
    )
