"""Chat-safe tools for Agent Brain (knowledge + live freshness hints)."""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool = True) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


def search_knowledge(
    query: str,
    *,
    tenant_id: str = "default",
    k: int = 3,
) -> list[str]:
    """Best-effort RAG snippets from the local knowledge base."""
    if not query.strip() or not _env_flag("OM_CHAT_RAG", True):
        return []
    try:
        from om_ai.knowledge.rag import PersistentKnowledgeBase

        kb = PersistentKnowledgeBase()
        try:
            hits = kb.search(query, tenant_id, k=k)
        except TypeError:
            hits = kb.search(query, k=k)
        out: list[str] = []
        for h in hits or []:
            text = getattr(h, "text", None) or (h.get("text") if isinstance(h, dict) else str(h))
            text = str(text or "").strip()
            if text:
                out.append(text[:240])
        return out
    except Exception as exc:
        logger.debug("knowledge search skipped: %s", exc)
        return []


def recall_memory(
    query: str,
    *,
    tenant_id: str = "default",
    actor: str = "",
    project_id: str | None = None,
    limit: int = 4,
) -> list[str]:
    if not actor or not _env_flag("OM_CHAT_MEMORY", True):
        return []
    try:
        from om_ai.runtime.intelligence import load_ui_memories

        rows = load_ui_memories(tenant_id, actor, project_id=project_id) or []
        snippets: list[str] = []
        q = (query or "").lower()
        for r in rows[:12]:
            content = str(r.get("content") or "").strip()
            if not content:
                continue
            if q and any(tok in content.lower() for tok in q.split()[:6]):
                snippets.insert(0, content)
            else:
                snippets.append(content)
            if len(snippets) >= limit:
                break
        return snippets[:limit]
    except Exception as exc:
        logger.debug("memory recall skipped: %s", exc)
        return []


def maybe_live_grounding(user_text: str, messages: list[dict[str, Any]]) -> str:
    """Optional live-knowledge grounded reply when freshness says so."""
    if not _env_flag("OM_LIVE_KNOWLEDGE", False):
        return ""
    try:
        from om_ai.live_knowledge import enrich_messages_for_live_knowledge

        _, meta = enrich_messages_for_live_knowledge(list(messages), force=False)
        grounded = str(meta.get("grounded_reply") or "").strip()
        if grounded and meta.get("prefer_grounded_reply"):
            return grounded[:800]
    except Exception as exc:
        logger.debug("live grounding skipped: %s", exc)
    return ""
