"""Optional reasoning layer bridge for task-mode turns."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ReasoningBridge:
    def assist(
        self,
        message: str,
        *,
        semantic: dict[str, Any],
        context_blob: str = "",
    ) -> dict[str, Any]:
        if not semantic.get("requires_action"):
            return {"used": False, "hint": ""}
        try:
            from om_ai.core.reasoning import run_reasoning_pipeline

            pack = run_reasoning_pipeline(message) or {}
            hint = str(pack.get("answer") or pack.get("plan") or context_blob)[:1000]
            return {"used": bool(hint), "hint": hint, "meta": pack.get("meta")}
        except Exception as exc:
            logger.debug("reasoning_bridge: %s", exc)
            return {"used": False, "hint": "", "error": str(exc)}
