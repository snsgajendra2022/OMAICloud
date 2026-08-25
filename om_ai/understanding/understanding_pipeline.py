"""OM Cognitive Understanding Layer v1 — meaning before generation."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any

from om_ai.understanding.context_analyzer import ContextSnapshot, analyze_context
from om_ai.understanding.intent_detector import IntentResult, detect_intent
from om_ai.understanding.meaning_parser import MeaningResult, parse_meaning
from om_ai.understanding.typo_corrector import correct_typos


def _env_flag(name: str, default: bool = True) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


@dataclass
class UnderstandingResult:
    original: str
    corrected: str
    understood_meaning: str
    goal: str
    intent: str
    category: str
    needs_solution: bool
    confidence: float
    plan_steps: list[str] = field(default_factory=list)
    context_summary: str = ""
    system_hint: str = ""
    public_understanding: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _plan_for(intent: str, goal: str) -> list[str]:
    base = [
        "Confirm understood meaning",
        "Identify missing details if any",
        "Propose a practical solution",
        "Verify the answer matches the user's goal",
    ]
    if intent == "debugging":
        return [
            "Restate the failure clearly",
            "List likely causes",
            "Propose a minimal fix",
            "Suggest how to verify",
        ]
    if intent == "understanding_feature":
        return [
            "Acknowledge the understanding requirement",
            "Describe the cognitive pipeline",
            "Map modules to implement",
            "Explain how replies improve",
        ]
    if intent == "ui_design":
        return [
            "Clarify the UI goal",
            "Suggest concrete visual/UX changes",
            "Outline implementation steps",
        ]
    if intent == "coding":
        return [
            "Clarify the coding goal",
            "Outline files/components involved",
            "Provide implementation guidance",
            "Suggest tests",
        ]
    if intent == "completion":
        return [
            "List remaining completion gaps",
            "Prioritize next milestones",
            "Propose an actionable sequence",
        ]
    if goal:
        return base
    return base


def _public_understanding(meaning: MeaningResult, intent: IntentResult) -> str:
    """User-visible acknowledgement (not private chain-of-thought)."""
    if intent.intent == "greeting":
        return ""
    if meaning.confidence < 0.7:
        return ""
    # Keep short for tiny context + UI.
    return f"Understanding: {meaning.understood_meaning}"


def _system_hint(u: UnderstandingResult) -> str:
    parts = [
        f"Understood: {u.understood_meaning}",
        f"Goal: {u.goal}",
        f"Intent: {u.intent}/{u.category}",
    ]
    if u.context_summary:
        parts.append(u.context_summary[:100])
    if u.plan_steps:
        parts.append("Plan: " + " → ".join(u.plan_steps[:3]))
    parts.append("Reply to the understood meaning, not the typos.")
    return "\n".join(parts)


class UnderstandingPipeline:
    """Run typo → intent → meaning → context → plan (self-owned, no API LLM)."""

    def run(
        self,
        user_text: str,
        *,
        messages: list[dict[str, Any]] | None = None,
        project_instructions: str = "",
        memory_snippets: list[str] | None = None,
    ) -> UnderstandingResult:
        original = (user_text or "").strip()
        if not _env_flag("OM_UNDERSTANDING", True) or not original:
            corrected = correct_typos(original) if original else ""
            return UnderstandingResult(
                original=original,
                corrected=corrected or original,
                understood_meaning=original,
                goal="",
                intent="chat",
                category="general",
                needs_solution=False,
                confidence=0.0,
                meta={"disabled": not _env_flag("OM_UNDERSTANDING", True)},
            )

        corrected = correct_typos(original)
        intent = detect_intent(corrected)
        # Also try original in case correction removed a signal.
        intent_raw = detect_intent(original)
        if intent_raw.confidence > intent.confidence:
            intent = intent_raw

        meaning = parse_meaning(original, intent=intent)
        ctx: ContextSnapshot = analyze_context(
            messages,
            project_instructions=project_instructions,
            memory_snippets=memory_snippets,
        )
        plan = _plan_for(intent.intent, meaning.goal)
        result = UnderstandingResult(
            original=original,
            corrected=meaning.corrected,
            understood_meaning=meaning.understood_meaning,
            goal=meaning.goal,
            intent=intent.intent,
            category=intent.category,
            needs_solution=intent.needs_solution,
            confidence=meaning.confidence,
            plan_steps=plan,
            context_summary=ctx.summary,
            meta={
                "tokens_changed": meaning.corrected.lower() != original.lower(),
                "context_users": len(ctx.recent_user),
            },
        )
        result.public_understanding = _public_understanding(meaning, intent)
        result.system_hint = _system_hint(result)
        return result


def understand_message(
    user_text: str,
    *,
    messages: list[dict[str, Any]] | None = None,
    project_instructions: str = "",
    memory_snippets: list[str] | None = None,
) -> UnderstandingResult:
    return UnderstandingPipeline().run(
        user_text,
        messages=messages,
        project_instructions=project_instructions,
        memory_snippets=memory_snippets,
    )
