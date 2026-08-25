"""Per-request feature flags from user Settings (overrides env defaults)."""
from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

_OVERRIDES: ContextVar[dict[str, bool] | None] = ContextVar("om_session_flags", default=None)

# Map Settings keys → OM_* env names used across agent/intelligence.
SETTINGS_TO_ENV = {
    "memory_enabled": "OM_CHAT_MEMORY",
    "rag_enabled": "OM_CHAT_RAG",
    "live_knowledge_enabled": "OM_LIVE_KNOWLEDGE",
    "agent_brain_enabled": "OM_AGENT_BRAIN",
}


def env_flag(name: str, default: bool = True) -> bool:
    """Resolve a feature flag: session override → process env → default."""
    ov = _OVERRIDES.get()
    if ov is not None and name in ov:
        return bool(ov[name])
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


def flags_from_settings(settings: dict[str, Any] | None) -> dict[str, bool]:
    """Build OM_* overrides from persisted user settings."""
    s = settings or {}
    llm_enabled = s.get("llm_enabled", True) is not False
    llm_only = bool(s.get("llm_only"))
    out: dict[str, bool] = {}
    if not llm_enabled:
        # Master off: disable model-side intelligence layers.
        out["OM_CHAT_MEMORY"] = False
        out["OM_CHAT_RAG"] = False
        out["OM_LIVE_KNOWLEDGE"] = False
        out["OM_AGENT_BRAIN"] = False
        return out
    if llm_only:
        # Direct LLM replies only — no agent / RAG / live enrichment.
        out["OM_CHAT_MEMORY"] = bool(s.get("memory_enabled", True))
        out["OM_CHAT_RAG"] = False
        out["OM_LIVE_KNOWLEDGE"] = False
        out["OM_AGENT_BRAIN"] = False
        return out
    out["OM_CHAT_MEMORY"] = s.get("memory_enabled", True) is not False
    out["OM_CHAT_RAG"] = s.get("rag_enabled", True) is not False
    out["OM_LIVE_KNOWLEDGE"] = bool(s.get("live_knowledge_enabled", False))
    out["OM_AGENT_BRAIN"] = s.get("agent_brain_enabled", True) is not False
    return out


@contextmanager
def apply_session_flags(overrides: dict[str, bool] | None) -> Iterator[None]:
    token = _OVERRIDES.set(dict(overrides or {}))
    try:
        yield
    finally:
        _OVERRIDES.reset(token)
