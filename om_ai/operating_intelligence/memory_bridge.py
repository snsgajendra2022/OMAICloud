"""Memory bridge — multi-layer human-like memory for Absolute OS."""
from __future__ import annotations

from typing import Any


def recall_all(
    query: str,
    *,
    tenant_id: str = "default",
    user_id: str = "",
    project_id: str | None = None,
    k: int = 4,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "short_term": [],
        "conversation": [],
        "user": [],
        "project": [],
        "skill": [],
        "experience": [],
        "knowledge": [],
    }
    actor = user_id or ""
    # UI / chat memories
    try:
        from om_ai.agent.tools import recall_memory, search_knowledge

        out["conversation"] = recall_memory(
            query, tenant_id=tenant_id, actor=actor, project_id=project_id, limit=k
        )
        out["knowledge"] = search_knowledge(query, tenant_id=tenant_id, k=k)
    except Exception:
        pass

    # Layered memory store
    if actor:
        try:
            from om_ai.memory.layers import LayeredMemory

            mem = LayeredMemory(tenant_id=tenant_id, user_id=actor)
            for layer in ("user", "project", "skill", "experience", "short", "conversation"):
                hits = mem.recall(query, layer=layer, k=max(2, k // 2)) or []
                key = "short_term" if layer == "short" else layer
                for h in hits:
                    text = str(h.get("content") or h.get("text") or "").strip()
                    if text:
                        out[key].append(text[:240])
        except Exception:
            pass

    # Dataset brain as knowledge memory
    try:
        from om_ai.brain.dataset_engine import retrieve_answer

        hit = retrieve_answer(query)
        if hit and hit.get("answer"):
            out["knowledge"].insert(0, str(hit["answer"])[:900])
    except Exception:
        pass

    return out


def remember_experience(
    content: str,
    *,
    tenant_id: str = "default",
    user_id: str = "",
    layer: str = "experience",
) -> dict[str, Any]:
    if not user_id or not content.strip():
        return {"ok": False, "reason": "missing_user_or_content"}
    try:
        from om_ai.memory.layers import LayeredMemory

        mid = LayeredMemory(tenant_id=tenant_id, user_id=user_id).remember(
            layer if layer else "experience", content.strip()
        )
        return {"ok": True, "id": mid, "layer": layer}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
