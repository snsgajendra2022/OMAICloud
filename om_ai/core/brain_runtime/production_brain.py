from __future__ import annotations

import logging

from om_ai.core.chatgpt_runtime import OMBrainController, run_chatgpt_runtime
from om_ai.core.observability import (
    ActivityEvent,
    ActivityType,
    ObservabilityEngine,
)

logger = logging.getLogger("OMProductionBrain")


class OMProductionBrain:
    """
    Production brain front door — STEP 30 ChatGPT-like controller.

    User → Chat Intelligence → Brain Router → Response Intelligence → Answer
    """

    def __init__(self) -> None:
        self.observability = ObservabilityEngine()
        self.controller = OMBrainController()

    def process(self, message: str):
        trace = self.observability.start_trace()
        self.observability.log(
            trace,
            ActivityEvent(
                type=ActivityType.THINKING,
                title="Processing user request",
                description="STEP 30 OM Brain Controller",
                metadata={"message_length": len(message or "")},
            ),
        )

        pack = (
            self.controller.run(message)
            if self.controller
            else run_chatgpt_runtime(message)
        )

        self.observability.log(
            trace,
            ActivityEvent(
                type=ActivityType.RESPONSE,
                title="ChatGPT-like runtime completed",
                description="Understand → Solve → Improve → Answer",
                metadata={
                    "source": pack.get("source"),
                    "stages": list(pack.get("stages") or [])[:12],
                },
            ),
        )

        return {
            "trace_id": getattr(trace, "trace_id", None),
            "response": pack,
            "answer": pack.get("answer") or "",
            "context_blob": pack.get("context_blob") or "",
            "meta": pack.get("meta") or {},
            "stages": pack.get("stages") or [],
            "chat_intelligence": pack.get("chat_intelligence") or {},
        }
