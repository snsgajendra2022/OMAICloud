"""OM Human-like Conversation Engine — understand before answering."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ConversationState:
    language: str = "en"
    intent: str = "chat"
    emotion: str = "neutral"
    goal: str = ""
    technology: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_TECH = re.compile(
    r"\b(react|next\.?js|vue|angular|svelte|fastapi|flask|django|python|typescript|"
    r"javascript|node|sql|postgres|mongodb|docker|kubernetes|swift|kotlin)\b",
    re.I,
)


def detect_language(text: str) -> str:
    t = text or ""
    if re.search(r"[\u0900-\u097F]", t):
        return "hi"
    if re.search(r"[\u0600-\u06FF]", t):
        return "ar"
    return "en"


def detect_emotion(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in ("angry", "furious", "hate", "stupid", "useless", "गधा", "बेकार")):
        return "frustrated"
    if any(w in t for w in ("sad", "upset", "hurt", "lonely", "cry", "दुख")):
        return "sad"
    if any(w in t for w in ("thanks", "great", "awesome", "love", "खुश", "धन्यवाद")):
        return "positive"
    if any(w in t for w in ("urgent", "asap", "hurry", "critical", "broken", "crash")):
        return "urgent"
    if "?" in t or any(w in t for w in ("how", "what", "why", "explain")):
        return "curious"
    return "neutral"


def infer_technologies(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in _TECH.finditer(text or "")})


def classify_and_plan(
    text: str,
    *,
    messages: list[dict[str, Any]] | None = None,
    project_instructions: str = "",
    memory_snippets: list[str] | None = None,
) -> ConversationState:
    from om_ai.agent.intent import classify_intent
    from om_ai.cognitive import run_cognitive_pipeline

    cog = run_cognitive_pipeline(
        text,
        messages=messages,
        project_instructions=project_instructions,
        memory_snippets=memory_snippets,
    )
    work = (cog.corrected or text or "").strip()
    intent = classify_intent(work)

    state = ConversationState(
        language=cog.language,
        intent=cog.intent if cog.intent != "chat" else intent.value,
        emotion=cog.emotion,
        goal=cog.goal,
        technology=cog.technologies,
        plan=cog.plan,
        meta={
            "understanding": cog.meta.get("understanding", {}),
            "cognitive": cog.to_dict(),
            "audience": cog.audience,
            "ui_phases": cog.ui_phases,
        },
    )

    qlow = work.lower()
    if intent.value == "coding" or cog.intent == "coding" or any(
        w in qlow for w in ("ui", "page", "signup", "login", "dashboard", "api", "code")
    ):
        state.intent = "coding" if intent.value == "chat" else intent.value
        if not state.technology and any(
            w in qlow for w in ("ui", "page", "signup", "login", "frontend", "react")
        ):
            state.technology = ["react"]
            state.clarification = "Assuming React for UI unless you specify another stack."
        if not state.plan:
            state.plan = [
                "Understand UI/API requirements",
                "Choose stack (inferred or stated)",
                "Produce files + code",
                "Note validation and next tests",
            ]
    elif intent.value in {"knowledge", "agent"}:
        if not state.plan:
            state.plan = [
                "Retrieve knowledge/memory",
                "Reason and verify",
                "Answer clearly",
            ]
    elif not state.plan:
        state.plan = [
            "Understand meaning",
            "Use memory + knowledge if relevant",
            "Reply naturally",
        ]
    return state


def control_response_style(state: ConversationState) -> dict[str, Any]:
    """Hints for natural reply tone."""
    tone = "warm_professional"
    if state.emotion == "frustrated":
        tone = "calm_supportive"
    elif state.emotion == "urgent":
        tone = "direct_action"
    elif state.emotion == "positive":
        tone = "upbeat"
    return {
        "tone": tone,
        "language": state.language,
        "match_user_language": True,
        "never_pretend": True,
        "show_assumptions": bool(state.clarification),
    }
