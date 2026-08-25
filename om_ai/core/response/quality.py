"""Response quality gate — wraps chat orchestrator checks."""
from __future__ import annotations

from typing import Any


def check_quality(text: str, *, user_ask: str = "") -> dict[str, Any]:
    from om_ai.runtime.chat_orchestrator import is_low_quality_reply

    fail = is_low_quality_reply(text)
    return {
        "ok": not bool(fail),
        "reason": fail or "ok",
        "user_ask": (user_ask or "")[:200],
        "action": "use_reasoning_fallback" if fail else "accept",
    }


def ensure_quality(text: str, *, user_ask: str = "", intent: str = "chat") -> str:
    """Return text if OK, else structured reasoning/coding fallback."""
    q = check_quality(text, user_ask=user_ask)
    if q["ok"]:
        return text
    from om_ai.agent.verifier import compose_fallback

    return compose_fallback(intent=intent or "chat", user_text=user_ask or "")
