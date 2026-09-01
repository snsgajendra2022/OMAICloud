"""Execute Agent Brain plans: gather evidence, optionally run low-risk tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from om_ai.agent.planner import Plan, coding_plan, plan_as_bullets, plan_for_goal
from om_ai.agent.tools import maybe_live_grounding, recall_memory, search_knowledge


@dataclass
class ExecutionBundle:
    plan_bullets: list[str] = field(default_factory=list)
    knowledge_snippets: list[str] = field(default_factory=list)
    memory_snippets: list[str] = field(default_factory=list)
    grounded_reply: str = ""
    notes: list[str] = field(default_factory=list)


def execute_for_chat(
    user_text: str,
    *,
    intent: str,
    messages: list[dict[str, Any]] | None = None,
    tenant_id: str = "default",
    actor: str = "",
    project_id: str | None = None,
) -> ExecutionBundle:
    """Gather plan + memory + knowledge for one chat turn (no high-risk tools)."""
    bundle = ExecutionBundle()
    messages = messages or []

    if intent in {"knowledge", "agent", "coding", "chat"}:
        bundle.knowledge_snippets = search_knowledge(
            user_text, tenant_id=tenant_id, k=8
        )
        bundle.memory_snippets = recall_memory(
            user_text,
            tenant_id=tenant_id,
            actor=actor,
            project_id=project_id,
            limit=6,
        )
        # If dataset/RAG returned a strong long answer, use it as grounded reply
        if bundle.knowledge_snippets and len(bundle.knowledge_snippets[0]) > 200:
            top = bundle.knowledge_snippets[0]
            if top.startswith("**OM dataset brain**") or "Answer:" in top[:80]:
                bundle.grounded_reply = top
                bundle.notes.append("dataset_grounded")

    if intent in {"knowledge", "agent"}:
        grounded = maybe_live_grounding(user_text, messages)
        if grounded:
            bundle.grounded_reply = grounded
            bundle.notes.append("live_grounding")

    if intent == "coding":
        bundle.plan_bullets = coding_plan(user_text)
        bundle.notes.append("coding_plan")
    elif intent == "agent":
        plan: Plan = plan_for_goal(user_text)
        bundle.plan_bullets = plan_as_bullets(plan)
        bundle.notes.append("rule_plan")

    return bundle


def format_system_hint(bundle: ExecutionBundle) -> str:
    """Compact hint for the model (fits tiny context windows)."""
    parts: list[str] = []
    if bundle.memory_snippets:
        parts.append("Memory: " + " | ".join(bundle.memory_snippets[:2]))
    if bundle.knowledge_snippets:
        parts.append("Knowledge: " + " | ".join(s[:80] for s in bundle.knowledge_snippets[:2]))
    if bundle.plan_bullets:
        parts.append("Plan: " + " → ".join(bundle.plan_bullets[:4]))
    return "\n".join(parts)
