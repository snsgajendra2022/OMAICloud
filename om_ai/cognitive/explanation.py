"""Explanation intelligence — adjust depth and tone to the user."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ExplanationProfile:
    audience: str  # beginner | developer | expert
    tone: str
    use_analogy: bool
    use_jargon: bool
    structure: str  # short | structured | deep
    hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "audience": self.audience,
            "tone": self.tone,
            "use_analogy": self.use_analogy,
            "use_jargon": self.use_jargon,
            "structure": self.structure,
            "hint": self.hint,
        }


_BEGINNER = re.compile(
    r"\b(eli5|beginner|simple|basics|easy|plain english|like i'?m\s*5|"
    r"non.?technical|layman|explain simply)\b",
    re.I,
)
_EXPERT = re.compile(
    r"\b(expert|deep dive|internals|architecture|implementation details|"
    r"production.?grade|observability|rate limit|oauth|distributed|"
    r"low.?level|advanced)\b",
    re.I,
)
_SIMPLE_Q = re.compile(
    r"^(what is|who is|define|meaning of|is .+ a)\b",
    re.I,
)
_TECHNICAL = re.compile(
    r"\b(api|endpoint|middleware|schema|dockerfile|kubernetes|postgres|"
    r"typescript|react|fastapi|authentication|jwt|rbac|cache|latency)\b",
    re.I,
)


def detect_audience(
    text: str,
    *,
    intent: str = "chat",
    messages: list[dict[str, Any]] | None = None,
) -> str:
    t = (text or "").strip()
    hist = " ".join(
        str(m.get("content") or "")
        for m in (messages or [])[-4:]
        if str(m.get("role") or "") == "user"
    )
    combined = f"{hist} {t}"
    if _BEGINNER.search(combined):
        return "beginner"
    if _EXPERT.search(combined) or (intent in {"architecture", "debug"} and _TECHNICAL.search(t)):
        return "expert"
    if _SIMPLE_Q.match(t.strip()) and len(t.split()) <= 8:
        return "beginner"
    if intent in {"coding", "debug", "architecture"} or _TECHNICAL.search(t):
        return "developer"
    return "developer"


def build_explanation_profile(
    text: str,
    *,
    intent: str = "chat",
    emotion: str = "neutral",
    messages: list[dict[str, Any]] | None = None,
) -> ExplanationProfile:
    audience = detect_audience(text, intent=intent, messages=messages)
    tone = "warm_professional"
    if emotion == "frustrated":
        tone = "calm_supportive"
    elif emotion == "urgent":
        tone = "direct_action"

    if audience == "beginner":
        return ExplanationProfile(
            audience=audience,
            tone=tone,
            use_analogy=True,
            use_jargon=False,
            structure="short" if _SIMPLE_Q.match((text or "").strip()) else "structured",
            hint=(
                "Use plain language and one simple analogy when helpful. "
                "Avoid unexplained acronyms."
            ),
        )
    if audience == "expert":
        return ExplanationProfile(
            audience=audience,
            tone=tone,
            use_analogy=False,
            use_jargon=True,
            structure="deep",
            hint=(
                "Be precise and technical. Cover trade-offs, security, "
                "operational concerns, and verification."
            ),
        )
    # developer default
    structure = "structured" if intent in {"coding", "debug", "architecture", "knowledge"} else "short"
    return ExplanationProfile(
        audience=audience,
        tone=tone,
        use_analogy=False,
        use_jargon=True,
        structure=structure,
        hint="Use clear sections for technical answers; include code when relevant.",
    )


def format_for_audience(
    text: str,
    profile: ExplanationProfile,
    *,
    intent: str = "chat",
    understanding: str = "",
) -> str:
    """Light post-format — add structure headers when reply is flat."""
    raw = (text or "").strip()
    if not raw:
        return raw
    if profile.audience == "beginner" and re.search(r"\bapis?\b", f"{raw} {intent}", re.I):
        if "waiter" not in raw.lower():
            analogy = (
                "API is like a waiter between two systems: you order, it carries "
                "the request, the kitchen (server) prepares a response."
            )
            raw = f"{analogy}\n\n{raw}"
    if profile.structure == "short":
        return raw
    if re.search(r"(?m)^#{1,3}\s|```", raw):
        return raw
    if intent not in {"coding", "debug", "architecture", "knowledge"} and profile.audience != "expert":
        return raw

    sections: list[str] = []
    if understanding:
        sections.append(f"## Understanding\n{understanding.strip()}")
    if profile.audience == "expert":
        sections.append(f"## Analysis\n{raw}")
        sections.append("## Next steps\n- Verify in your environment\n- Add tests where applicable")
        return "\n\n".join(sections)
    if intent == "coding" and "```" in raw:
        sections.append(f"## Implementation\n{raw}")
        sections.append("## Testing\n- Happy path\n- Invalid input / edge cases")
        sections.append("## Next steps\n- Wire to your API\n- Do not commit secrets")
        return "\n\n".join(sections)
    return raw
