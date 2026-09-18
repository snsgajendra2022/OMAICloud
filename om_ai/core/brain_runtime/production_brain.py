from __future__ import annotations

import logging

from om_ai.core.brain_router import OMBrainRouter, run_om_brain_router
from om_ai.core.agent_runtime import OMAutonomousAgentRuntime, run_agent_runtime
from om_ai.core.chat_intelligence import ChatOrchestrator, run_chat_intelligence
from om_ai.core.observability import (
    ActivityEvent,
    ActivityType,
    ObservabilityEngine,
)

logger = logging.getLogger("OMProductionBrain")


class OMProductionBrain:
    """
    Main OM AI production brain — Chat Intelligence + Brain Router front door.

    Flow:
      User → Chat Intelligence → Fusion → Research → Knowledge →
      Agents → Answer Improvement → Response
    """

    def __init__(self) -> None:
        self.observability = ObservabilityEngine()
        self.chat_intelligence = ChatOrchestrator()
        self.router = OMBrainRouter()
        self.agent_runtime = OMAutonomousAgentRuntime()

    def process(self, message: str):
        trace = self.observability.start_trace()
        self.observability.log(
            trace,
            ActivityEvent(
                type=ActivityType.THINKING,
                title="Processing user request",
                description="STEP 26 Chat Intelligence + STEP 24 Brain Router",
                metadata={"message_length": len(message or "")},
            ),
        )

        chat = self.chat_intelligence.run(message) if self.chat_intelligence else run_chat_intelligence(message)
        if chat.get("answer") and not chat.get("needs_model", True):
            self.observability.log(
                trace,
                ActivityEvent(
                    type=ActivityType.RESPONSE,
                    title="Chat Intelligence social response",
                    description="Greeting/identity handled without raw model",
                    metadata={"intent": (chat.get("intent") or {}).get("intent")},
                ),
            )
            return {
                "trace_id": getattr(trace, "trace_id", None),
                "response": chat,
                "answer": chat.get("answer") or "",
                "context_blob": chat.get("context_blob") or "",
                "meta": chat.get("meta") or {},
                "stages": chat.get("stages") or [],
                "chat_intelligence": chat,
            }

        pack = self.router.run(message) if self.router else run_om_brain_router(message)

        sol = str((chat.get("solution") or {}).get("answer") or "").strip()
        if sol and isinstance(pack, dict):
            pack["context_blob"] = (
                str(pack.get("context_blob") or "") + "\n" + sol
            ).strip()[:6000]
            meta = dict(pack.get("meta") or {})
            meta["chat_intelligence"] = chat.get("meta") or {}
            pack["meta"] = meta
            if not pack.get("answer") and chat.get("answer"):
                pack["answer"] = chat.get("answer")

        step26 = pack.get("agent_runtime") if isinstance(pack, dict) else None
        if not isinstance(step26, dict) or not step26.get("stages"):
            step26 = (
                self.agent_runtime.run(message)
                if self.agent_runtime
                else run_agent_runtime(message)
            )
            if isinstance(pack, dict):
                pack["agent_runtime"] = step26

        self.observability.log(
            trace,
            ActivityEvent(
                type=ActivityType.RESPONSE,
                title="Chat Intelligence + Brain completed",
                description="Understand → Solve → Improve → Answer",
                metadata={
                    "models": list(pack.get("models") or []),
                    "intent": (chat.get("intent") or {}).get("intent"),
                    "research_used": bool(pack.get("research_used")),
                },
            ),
        )

        return {
            "trace_id": getattr(trace, "trace_id", None),
            "response": pack,
            "answer": pack.get("answer")
            or chat.get("answer")
            or (step26 or {}).get("answer")
            or "",
            "context_blob": pack.get("context_blob") or "",
            "meta": pack.get("meta") or {},
            "stages": list(chat.get("stages") or []) + list(pack.get("stages") or []),
            "chat_intelligence": chat,
            "step26": step26 or {},
        }
