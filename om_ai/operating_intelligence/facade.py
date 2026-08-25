"""Operating Intelligence facade: Observe → Understand → Think → Plan → Execute → Verify → Improve."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from om_ai.operating_intelligence.embodiment import electronics, robotics, sensors, twin


@dataclass
class CycleResult:
    goal: str
    observed: dict[str, Any] = field(default_factory=dict)
    understood: dict[str, Any] = field(default_factory=dict)
    plan: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)
    response: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def capability_status() -> dict[str, Any]:
    """Honest board: what is live vs stub in this install."""
    return {
        "system": "OM AI — Operating Intelligence",
        "cycle": ["observe", "understand", "think", "plan", "execute", "verify", "improve"],
        "capabilities": {
            "human_understanding": "partial",
            "memory": "exists",
            "reasoning_planning": "partial",
            "software_agents": "partial",
            "knowledge_rag": "exists",
            "response_experience": "exists",
            "voice": "partial",
            "vision": "partial",
            "continuous_learning": "partial",
            "foundation_model": "partial",
            "electronics_iot": electronics.status(),
            "sensors": sensors.status(),
            "robotics": robotics.status(),
            "digital_twin": twin.status(),
        },
        "note": (
            "JARVIS requires model+memory+tools+hardware. "
            "Embodiment modules are stubs until real drivers are connected."
        ),
        "docs": "docs/JARVIS_OPERATING_INTELLIGENCE.md",
    }


class OperatingIntelligence:
    """Thin orchestration layer — does not replace agents/runtime; connects them."""

    def run(
        self,
        goal: str,
        *,
        context: dict[str, Any] | None = None,
        dry_run: bool = True,
    ) -> CycleResult:
        return run_cycle(goal, context=context, dry_run=dry_run)


def run_cycle(
    goal: str,
    *,
    context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> CycleResult:
    """Execute one Observe→Improve cycle (digital-first; hardware gated)."""
    from om_ai.agent.intent import classify_intent
    from om_ai.agent.planner import coding_plan
    from om_ai.agent.verifier import compose_fallback, verify_reply
    from om_ai.response_engine import format_assistant_reply
    from om_ai.understanding.understanding_pipeline import understand_message

    ctx = context or {}
    goal = (goal or "").strip()
    result = CycleResult(goal=goal)

    # Observe
    result.observed = {
        "goal": goal,
        "context_keys": sorted(ctx.keys()),
        "dry_run": dry_run,
    }

    # Understand
    understanding = understand_message(goal)
    intent = classify_intent(goal)
    result.understood = {
        "intent": intent.value,
        "understanding": understanding.to_dict() if hasattr(understanding, "to_dict") else str(understanding),
    }

    # Think / Plan
    if intent.value == "coding":
        result.plan = coding_plan(goal)
    else:
        result.plan = [
            "Clarify goal and constraints",
            "Gather memory/knowledge context",
            "Propose solution",
            "Validate before acting",
        ]

    # Execute (digital tools only here; hardware requires explicit enable)
    actions: list[dict[str, Any]] = []
    if ctx.get("allow_hardware") and not dry_run:
        actions.append(
            {
                "type": "hardware",
                "status": "blocked_or_stub",
                "detail": electronics.command({"op": "status"}, dry_run=True),
            }
        )
    else:
        actions.append(
            {
                "type": "digital",
                "status": "planned",
                "steps": result.plan,
            }
        )
    result.actions = actions

    # Verify + respond
    draft = compose_fallback(
        intent=intent.value if intent.value in {"greeting", "coding", "agent", "knowledge", "identity"} else "chat",
        user_text=goal,
        plan_bullets=result.plan,
    )
    reason = verify_reply(draft, intent=intent.value)
    result.verification = {"ok": not reason, "reason": reason or ""}
    result.response = format_assistant_reply(draft, intent=intent.value)
    result.meta = {
        "layer": "operating_intelligence",
        "hardware_enabled": bool(ctx.get("allow_hardware")) and not dry_run,
        "capabilities": capability_status()["capabilities"],
    }
    return result
