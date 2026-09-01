"""Session memory — short-term window + durable preference/project writes."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def record_turn(
    user_text: str,
    *,
    tenant_id: str = "default",
    user_id: str = "",
    project_id: str | None = None,
    goal: str = "",
    stack: list[str] | None = None,
) -> dict[str, Any]:
    """Persist this turn into short-term + optional project memory."""
    if not (user_text or "").strip():
        return {"ok": False, "reason": "empty"}
    stored: dict[str, Any] = {"short": False, "project": False, "preference": False, "experience": False}
    actor = user_id or "anonymous"
    try:
        from om_ai.memory.layers import LayeredMemory

        mem = LayeredMemory(tenant_id=tenant_id, user_id=actor)
        body = goal.strip() if goal.strip() else user_text.strip()[:400]
        mem.remember("short", f"User: {user_text.strip()[:240]}\nGoal: {body[:240]}")
        stored["short"] = True
        if project_id or (stack and goal):
            mem.remember(
                "project",
                f"Project {project_id or 'session'}: {body[:200]}\nStack: {', '.join(stack or [])}",
                metadata={"project_id": project_id or "", "stack": stack or []},
            )
            stored["project"] = True
            mem.remember(
                "experience",
                f"Decision: {body[:240]}",
                metadata={"kind": "turn"},
            )
            stored["experience"] = True
        from om_ai.runtime.intelligence import extract_memory_candidates

        for cand in extract_memory_candidates(user_text) or []:
            mem.remember("user", str(cand.get("content") or ""), metadata=cand)
            stored["preference"] = True
    except Exception as exc:
        logger.debug("record_turn failed: %s", exc)
        stored["error"] = str(exc)
    return {"ok": stored.get("short", False), **stored}
