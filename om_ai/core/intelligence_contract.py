"""Deterministic preflight signals for OM AI's intelligence runtime.

This module provides routing hints, not deep reasoning or psychological diagnosis.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable, Literal

Intent = Literal["greeting", "coding", "learning", "writing", "research", "decision", "action", "general"]
Emotion = Literal["possible_frustration", "possible_confusion", "possible_urgency", "positive_tone", "distress_signal", "unknown"]
Strategy = Literal["answer_directly", "explain_stepwise", "inspect_and_debug", "draft_content", "research_and_verify", "compare_options", "respond_with_empathy", "clarify_before_action", "general_response"]

_PATTERNS = (
    ("greeting", re.compile(r"^\s*(hi|hello|hey|good morning|good afternoon|good evening)\b", re.I)),
    ("coding", re.compile(r"\b(code|coding|bug|error|exception|stack trace|compile|build failed|debug|api|function|class|typescript|python|react|ionic|capacitor|git|repository|test failed)\b", re.I)),
    ("learning", re.compile(r"\b(explain|teach me|learn|how does .* work|step by step|beginner)\b", re.I)),
    ("writing", re.compile(r"\b(write|rewrite|rephrase|draft|correct (my )?(message|sentence|email)|email|status report|summary)\b", re.I)),
    ("research", re.compile(r"\b(latest|current|research|sources|citation|look up|search the web|verify this fact)\b", re.I)),
    ("decision", re.compile(r"\b(compare|recommend|pros and cons|versus|vs\.?)\b", re.I)),
    ("action", re.compile(r"\b(delete|send|publish|deploy|purchase|transfer|commit|push|merge|run this command)\b", re.I)),
)
_EMOTION_PATTERNS = (
    ("distress_signal", re.compile(r"\b(i want to die|kill myself|suicide|hurt myself)\b", re.I)),
    ("possible_frustration", re.compile(r"\b(still not working|doesn't work|does not work|tried many times|frustrat|useless|broken again)\b", re.I)),
    ("possible_confusion", re.compile(r"\b(i don't understand|i do not understand|confused|what do you mean|not clear)\b", re.I)),
    ("possible_urgency", re.compile(r"\b(urgent|asap|right now|today deadline|production is down|release today)\b", re.I)),
    ("positive_tone", re.compile(r"\b(great|awesome|finally working|thank you so much|excellent)\b", re.I)),
)
_STRATEGIES = {
    "greeting": "answer_directly", "coding": "inspect_and_debug",
    "learning": "explain_stepwise", "writing": "draft_content",
    "research": "research_and_verify", "decision": "compare_options",
    "action": "clarify_before_action", "general": "general_response",
}

@dataclass(frozen=True)
class TurnAssessment:
    intent: str
    emotion: str
    strategy: str
    language_hint: str
    needs_clarification: bool
    clarification_reason: str | None
    high_impact_action: bool
    signals: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["signals"] = list(self.signals)
        return result

def assess_user_turn(text: str, *, history: Iterable[str] = (), language_hint: str = "auto") -> TurnAssessment:
    """Return conservative routing hints without rewriting the user's message.

    Labels are heuristic and are not calibrated confidence scores. History is
    accepted for API stability but intentionally unused in this first baseline.
    """
    del history
    clean = text.strip() if isinstance(text, str) else ""
    signals: list[str] = []
    if not clean:
        return TurnAssessment("general", "unknown", "general_response", language_hint, True,
            "The message is empty; ask what the user needs.", False, ("empty_input",))

    intent = "general"
    for label, pattern in _PATTERNS:
        if pattern.search(clean):
            intent = label
            signals.append("intent_pattern:" + label)
            break

    emotion = "unknown"
    for label, pattern in _EMOTION_PATTERNS:
        if pattern.search(clean):
            emotion = label
            signals.append("emotion_cue:" + label)
            break
    if emotion in ("possible_confusion", "distress_signal", "possible_frustration"):
        signals.append("use_gentle_nonjudgmental_tone")

    lower = clean.casefold()
    high_impact = any(term in lower for term in (
        "delete all", "drop database", "rm -rf", "transfer money",
        "send to everyone", "publish to production", "deploy to production",
        "merge to main", "revoke access",
    ))
    needs_clarification = intent == "action" and high_impact
    reason = ("Potentially consequential action: verify target, scope, and authorization before execution."
              if needs_clarification else None)
    if needs_clarification:
        signals.append("confirmation_required")
    if clean.endswith("?") and len(clean.split()) < 5 and re.search(r"\b(it|that|this)\b", clean, re.I):
        needs_clarification = True
        reason = reason or "The reference may be ambiguous; use context or ask one focused question."
        signals.append("possible_ambiguous_reference")

    strategy = "respond_with_empathy" if emotion == "distress_signal" else _STRATEGIES[intent]
    return TurnAssessment(intent, emotion, strategy, language_hint, needs_clarification,
        reason, high_impact, tuple(signals))

def assess_answer_quality(*, answer: str, user_request: str, tool_error: bool = False) -> dict[str, object]:
    """Run basic integrity checks; this is not a factual truth detector."""
    response = answer.strip() if isinstance(answer, str) else ""
    request = user_request.strip() if isinstance(user_request, str) else ""
    issues: list[str] = []
    if not response:
        issues.append("empty_answer")
    if tool_error:
        issues.append("tool_execution_failed")
    if not request:
        issues.append("missing_original_request")
    if response and response.casefold() in {request.casefold(), "i don't know", "i do not know", "error", "failed"}:
        issues.append("possible_echo_or_non_answer")
    return {
        "passed_basic_checks": not issues,
        "issues": issues,
        "requires_independent_verification": bool(response),
        "limitations": [
            "These checks do not establish factual truth, reasoning correctness, or user satisfaction.",
            "Use domain-specific tools, tests, sources, or a separately evaluated model for verification.",
        ],
    }
