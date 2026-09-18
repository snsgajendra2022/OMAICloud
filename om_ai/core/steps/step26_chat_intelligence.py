"""STEP 26 — OM Chat Intelligence Core."""
from __future__ import annotations

from om_ai.core.chat_intelligence import ChatOrchestrator, run_chat_intelligence

__all__ = ["ChatOrchestrator", "run_chat_intelligence", "Step26ChatIntelligence"]


class Step26ChatIntelligence(ChatOrchestrator):
    """Alias for roadmap naming."""

    step = 26
