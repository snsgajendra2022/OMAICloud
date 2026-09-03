"""Route intent → capability. Registry lookup only — no keyword branches."""
from __future__ import annotations

from typing import Any, Callable


# Intent → capability id. Expand by registering, not by if music / if date.
INTENT_CAPABILITY: dict[str, str] = {
    "vision_analysis": "vision",
    "date_request": "date",
    "prompt_generation": "prompt_generator",
    "recommendation": "recommendation",
    "code_creation": "coding",
    "explanation": "research",
    "debugging": "coding",
    "research": "research",
    "planning": "planning",
    "comparison": "analysis",
    "calculation": "calculator",
    "conversation": "chat",
    "question": "research",
    "creation": "coding",
    "generation": "prompt_generator",
    "unclear": "clarify",
}


def _cap_date(_q: str, _ctx: dict, _u: dict) -> str:
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        now = datetime.now().astimezone()
    return f"Today's date is {now.strftime('%A, %d %B %Y')}.\n"


def _cap_prompt(q: str, ctx: dict, u: dict) -> str:
    topic = q
    for noise in ("create prompt for", "make prompt for", "write prompt for", "generate prompt for", "create prompt", "make prompt"):
        if noise in q.lower():
            topic = q.lower().split(noise, 1)[-1].strip(" :.-")
            break
    topic = topic or "the requested task"
    project = str(ctx.get("project_hint") or "").strip()
    extra = f"\nProject context: {project}." if project else ""
    return (
        "## Reusable AI Prompt\n\n"
        f"You are an expert assistant helping with **{topic}**.\n\n"
        "Goals:\n"
        "- Produce production-quality output\n"
        "- Explain architecture briefly before code\n"
        "- Prefer TypeScript when building UI\n"
        "- Include file structure and key snippets\n"
        "- List run/test steps\n\n"
        "Constraints:\n"
        "- No placeholder-only stubs\n"
        "- Call out assumptions\n"
        f"- Stay focused on: {topic}\n"
        f"{extra}\n"
        "Output format:\n"
        "1. Summary\n"
        "2. Architecture\n"
        "3. File tree\n"
        "4. Code\n"
        "5. Next steps\n"
    )


def _cap_recommendation(q: str, ctx: dict, u: dict) -> str:
    domain = str(u.get("domain") or "")
    if domain == "music" or "playlist" in q.lower() or "music" in q.lower():
        return (
            "Here are playlist name ideas:\n\n"
            "**Coding / Focus**\n"
            "- Deep Focus Flow\n"
            "- Lo-Fi Commit Messages\n"
            "- Midnight Refactor\n\n"
            "**Workout**\n"
            "- Energy Boost\n"
            "- PR Power Hour\n\n"
            "**Relax**\n"
            "- Calm Evening\n"
            "- Soft Reset\n\n"
            "Want names tuned to a mood, genre, or activity?\n"
        )
    return (
        "Here are recommendation options based on your request:\n\n"
        "1. Top picks for a quick start\n"
        "2. Alternatives if you want variety\n"
        "3. A shortlist to refine further\n\n"
        "Share a preference (mood, budget, or goal) and I’ll narrow it.\n"
    )


def _cap_coding(q: str, ctx: dict, u: dict) -> str:
    return (
        f"I can help implement this: **{q.strip()}**.\n\n"
        "## Plan\n"
        "1. Confirm stack and constraints\n"
        "2. Outline structure\n"
        "3. Implement the core path\n"
        "4. Add tests\n\n"
        "Reply with framework preferences (e.g. React/Next, auth, API) and I’ll generate concrete code.\n"
    )


def _cap_research(q: str, ctx: dict, u: dict) -> str:
    try:
        from om_ai.knowledge.facts import lookup_fact
        hit = lookup_fact(q)
        if hit and hit.get("answer"):
            return str(hit["answer"]).strip() + "\n"
    except Exception:
        pass
    return (
        f"**Topic:** {q.strip()}\n\n"
        "Here’s a clear take:\n"
        "- Core idea\n"
        "- How it works\n"
        "- Why it matters\n"
        "- Practical takeaway\n\n"
        "Want a beginner version or a deeper technical dive?\n"
    )


def _cap_planning(q: str, ctx: dict, u: dict) -> str:
    return (
        f"**Plan for:** {q.strip()}\n\n"
        "1. Define the outcome\n"
        "2. Break into milestones\n"
        "3. Sequence the first 3 actions\n"
        "4. Set a check-in point\n\n"
        "Share timeline/constraints for a tighter plan.\n"
    )


def _cap_analysis(q: str, ctx: dict, u: dict) -> str:
    return (
        f"**Analysis focus:** {q.strip()}\n\n"
        "- Current state\n"
        "- Options\n"
        "- Trade-offs\n"
        "- Recommendation\n\n"
        "Add criteria (cost, speed, quality) if you want a ranked choice.\n"
    )


def _cap_calculator(q: str, ctx: dict, u: dict) -> str:
    return (
        "I can compute that. Paste the exact expression or numbers "
        "(for example `15% of 2400`) and I’ll calculate it.\n"
    )


def _cap_chat(q: str, ctx: dict, u: dict) -> str:
    return "Hello — I’m OM. What should we work on?\n"


def _cap_clarify(q: str, ctx: dict, u: dict) -> str:
    return (
        f"I want to make sure I help correctly with “{q.strip()}”.\n\n"
        "Do you want me to:\n"
        "1. Explain it\n"
        "2. Create something (code / prompt / plan)\n"
        "3. Recommend options\n"
        "4. Something else — tell me the goal in one sentence\n"
    )


def _cap_vision(q: str, ctx: dict, u: dict) -> str:
    return (
        "I can analyze that visual.\n\n"
        "Upload/attach the image (or screenshot), then ask what you need:\n"
        "- What is in this image?\n"
        "- Extract text / fields\n"
        "- What is wrong / how to improve?\n"
        "- Create a similar design brief\n"
    )


CAPABILITY_HANDLERS: dict[str, Callable[[str, dict, dict], str]] = {
    "date": _cap_date,
    "prompt_generator": _cap_prompt,
    "recommendation": _cap_recommendation,
    "coding": _cap_coding,
    "research": _cap_research,
    "planning": _cap_planning,
    "analysis": _cap_analysis,
    "calculator": _cap_calculator,
    "chat": _cap_chat,
    "clarify": _cap_clarify,
    "vision": _cap_vision,
}


class CapabilityRouter:
    def route(self, intent: dict[str, Any]) -> dict[str, Any]:
        key = str(intent.get("intent") or intent.get("canonical") or "unclear")
        cap = INTENT_CAPABILITY.get(key) or INTENT_CAPABILITY.get(str(intent.get("canonical"))) or "clarify"
        return {
            "capability": cap,
            "handler": CAPABILITY_HANDLERS.get(cap, _cap_clarify),
            "intent": key,
        }

    def execute(
        self,
        capability: dict[str, Any],
        question: str,
        context: dict[str, Any],
        understanding: dict[str, Any],
    ) -> str:
        fn = capability.get("handler") or _cap_clarify
        return str(fn(question, context, understanding) or "").strip() + "\n"
