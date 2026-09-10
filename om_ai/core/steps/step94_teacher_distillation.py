"""STEP 94 — OM Multi-LLM Teacher Distillation Intelligence.

Harvest connected teacher LLM answers → clean/verify/rank → SFT/DPO export.
Separate from the chat Provider Layer (which only routes live replies).
"""
from __future__ import annotations

import os
from typing import Any

from om_ai.core.distillation import TeacherManager


class TeacherDistillationIntelligence:
    """Brain/roadmap facade for STEP 94."""

    def __init__(self) -> None:
        self.enabled = os.getenv("OM_DISTILL_ON_LEARN", "0").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
        self.manager = TeacherManager(allow_mock=True)

    def harvest(self, task: str, *, teachers: list[str] | None = None) -> dict[str, Any]:
        return self.manager.collect_and_save(task, teachers=teachers)

    def learn_from_turn(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Optional hook: only runs when OM_DISTILL_ON_LEARN=1 and quality is high.

        Does not call external teachers on every chat by default (cost/latency).
        Use ``om-ai distill`` / ``llm_harvest`` for deliberate harvesting.
        """
        quality = quality or {}
        score = float(quality.get("score") or 0.0)
        if not self.enabled:
            return {"step": 94, "skipped": True, "reason": "OM_DISTILL_ON_LEARN=0"}
        if score < 0.7 or len((question or "").strip()) < 40:
            return {"step": 94, "skipped": True, "reason": "quality_or_length_gate"}
        # Queue the question for offline harvest rather than blocking chat.
        try:
            result = self.manager.collect(question)
            saved = self.manager.save(result)
            return {"step": 94, "queued": True, "run_id": saved.get("run_id"), "export": saved.get("export")}
        except Exception as exc:
            return {"step": 94, "error": str(exc)}

    def status(self) -> dict[str, Any]:
        meta = self.manager.state.load_meta()
        return {
            "step": 94,
            "name": "Multi-LLM Teacher Distillation",
            "enabled_on_learn": self.enabled,
            "state": meta,
            "output_root": str(self.manager.state.root),
            "honest_limit": (
                "Learns from teacher API outputs you are licensed to use. "
                "Does not extract private model weights. Quality still depends on "
                "teacher answers + OM training compute."
            ),
        }
