"""OM Human-Like Cognitive Pipeline — understand meaning before answering.

Flow:
  User input → spelling → language → intent → meaning → context → goal
  → knowledge profile → reasoning plan → explanation profile → answer hints
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from om_ai.cognitive.explanation import (
    ExplanationProfile,
    build_explanation_profile,
    format_for_audience,
)
from om_ai.cognitive.goal_detector import GoalResult, detect_goal
from om_ai.understanding import understand_message


@dataclass
class CognitiveState:
    original: str
    corrected: str
    language: str
    understood_meaning: str
    goal: str
    resolved_text: str
    intent: str
    category: str
    emotion: str
    audience: str
    response_structure: str
    plan: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    context_summary: str = ""
    project_topic: str = ""
    public_understanding: str = ""
    system_hint: str = ""
    ui_phases: list[str] = field(default_factory=list)
    explanation: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ui_phases(state: CognitiveState) -> list[str]:
    phases = ["Understanding your message…"]
    if state.context_summary or state.project_topic:
        phases.append("Checking conversation context…")
    if state.intent in {"coding", "debug", "architecture"}:
        phases.append("Planning architecture…")
        phases.append("Preparing implementation…")
    elif state.intent in {"knowledge", "agent"}:
        phases.append("Searching knowledge…")
    else:
        phases.append("Thinking…")
    phases.append("Checking answer quality…")
    return phases


class CognitivePipeline:
    """Single entry for human-like understanding before any generation."""

    def run(
        self,
        user_text: str,
        *,
        messages: list[dict[str, Any]] | None = None,
        project_instructions: str = "",
        memory_snippets: list[str] | None = None,
    ) -> CognitiveState:
        from om_ai.conversation_engine import (
            detect_emotion,
            detect_language,
            infer_technologies,
        )

        original = (user_text or "").strip()
        u = understand_message(
            original,
            messages=messages,
            project_instructions=project_instructions,
            memory_snippets=memory_snippets,
        )
        lang = detect_language(u.corrected or original)
        emotion = detect_emotion(u.corrected or original)
        techs = infer_technologies(u.corrected or original)
        if not techs and messages:
            hist = " ".join(
                str(m.get("content") or "")
                for m in messages[-6:]
                if str(m.get("role") or "") == "user"
            )
            techs = infer_technologies(hist)

        goal_r: GoalResult = detect_goal(
            original,
            messages=messages,
            corrected=u.corrected,
            base_goal=u.goal,
        )
        profile: ExplanationProfile = build_explanation_profile(
            u.corrected or original,
            intent=u.intent,
            emotion=emotion,
            messages=messages,
        )

        understood = u.understood_meaning
        if goal_r.used_context and goal_r.project_topic:
            understood = (
                f"{u.understood_meaning} "
                f"(Context: continuing work on {goal_r.project_topic})"
            ).strip()

        plan = list(u.plan_steps or [])
        if u.intent == "coding" and len(plan) < 4:
            plan = [
                "Clarify requirements and stack",
                "Outline frontend, backend, data, and security",
                "Implement with validation",
                "Suggest tests and deployment steps",
            ]

        hint_parts = [
            f"Understood: {goal_r.resolved_text or u.corrected}",
            f"Goal: {goal_r.goal}",
            f"Intent: {u.intent}",
            f"Audience: {profile.audience}",
            profile.hint,
        ]
        if u.context_summary:
            hint_parts.append(u.context_summary[:120])
        if techs:
            hint_parts.append("Stack: " + ", ".join(techs))
        hint_parts.append("Answer the user's meaning, not typos.")

        pub = u.public_understanding
        if goal_r.used_context and pub:
            pub = f"{pub} (in context of your ongoing project)"

        state = CognitiveState(
            original=original,
            corrected=u.corrected,
            language=lang,
            understood_meaning=understood,
            goal=goal_r.goal,
            resolved_text=goal_r.resolved_text,
            intent=u.intent,
            category=u.category,
            emotion=emotion,
            audience=profile.audience,
            response_structure=profile.structure,
            plan=plan,
            technologies=techs,
            context_summary=u.context_summary,
            project_topic=goal_r.project_topic,
            public_understanding=pub,
            system_hint="\n".join(h for h in hint_parts if h),
            explanation=profile.to_dict(),
            meta={
                "understanding": u.to_dict(),
                "goal_confidence": goal_r.confidence,
                "used_context": goal_r.used_context,
            },
        )
        state.ui_phases = _ui_phases(state)
        return state


def run_cognitive_pipeline(
    user_text: str,
    *,
    messages: list[dict[str, Any]] | None = None,
    project_instructions: str = "",
    memory_snippets: list[str] | None = None,
) -> CognitiveState:
    return CognitivePipeline().run(
        user_text,
        messages=messages,
        project_instructions=project_instructions,
        memory_snippets=memory_snippets,
    )


def polish_reply(state: CognitiveState, reply: str) -> str:
    """Apply explanation + audience formatting to a draft reply."""
    profile = ExplanationProfile(
        audience=state.audience,
        tone=state.explanation.get("tone", "warm_professional"),
        use_analogy=bool(state.explanation.get("use_analogy")),
        use_jargon=bool(state.explanation.get("use_jargon")),
        structure=state.response_structure,
        hint=str(state.explanation.get("hint") or ""),
    )
    formatted = format_for_audience(
        reply,
        profile,
        intent=state.intent,
        understanding=state.public_understanding or state.understood_meaning[:200],
    )
    try:
        from om_ai.core.response.format_engine import format_reply

        formatted = format_reply(
            formatted,
            state.resolved_text or state.original,
            intent=state.intent,
            audience=state.audience,
            understanding=state.public_understanding or state.understood_meaning[:200],
        )
    except Exception:
        pass
    return formatted


__all__ = [
    "CognitivePipeline",
    "CognitiveState",
    "run_cognitive_pipeline",
    "polish_reply",
]
