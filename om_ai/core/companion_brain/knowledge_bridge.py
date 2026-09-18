"""Optional knowledge brain bridge."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class KnowledgeBridge:
    def enrich(self, message: str, *, semantic: dict[str, Any]) -> dict[str, Any]:
        domain = semantic.get("domain") or "general"
        if domain == "general" and not semantic.get("requires_action"):
            return {"used": False, "blob": ""}
        try:
            from om_ai.core.knowledge_brain import KnowledgeBrain

            out = KnowledgeBrain().analyze(message) or {}
            blob = str(out.get("summary") or out.get("context") or "")[:1200]
            return {"used": bool(blob), "blob": blob, "raw": out}
        except Exception as exc:
            logger.debug("knowledge_bridge: %s", exc)
            return {"used": False, "blob": "", "error": str(exc)}
