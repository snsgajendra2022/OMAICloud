"""STEP 94 — OM Multi-LLM Teacher Distillation Intelligence (+ 94.10–94.14).

Harvest connected teacher LLM answers → clean/verify/rank → SFT/DPO export.
Extensions:
  94.10 Teacher Intelligence
  94.11 Curriculum Generator
  94.12 Autonomous Harvest Scheduler
  94.13 Knowledge Gap Collector
  94.14 Continuous Distillation Loop
"""
from __future__ import annotations

import os
from typing import Any

from om_ai.core.distillation import TeacherManager
from om_ai.core.distillation.continuous_loop import ContinuousDistillationLoop
from om_ai.core.distillation.curriculum_generator import CurriculumGenerator
from om_ai.core.distillation.factory import create_continuous_loop
from om_ai.core.distillation.harvest_scheduler import AutonomousHarvestScheduler
from om_ai.core.distillation.knowledge_gap_collector import KnowledgeGapCollector
from om_ai.core.distillation.teacher_intelligence import TeacherIntelligence


class TeacherDistillationIntelligence:
    """Brain/roadmap facade for STEP 94 + substeps 94.10–94.14."""

    def __init__(self) -> None:
        self.enabled = os.getenv("OM_DISTILL_ON_LEARN", "0").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
        self.manager = TeacherManager(allow_mock=True)
        self.teacher_intel = TeacherIntelligence()
        self.curriculum = CurriculumGenerator()
        self.scheduler = AutonomousHarvestScheduler()
        self.gaps = KnowledgeGapCollector()
        self.loop = ContinuousDistillationLoop(
            gaps=self.gaps,
            curriculum=self.curriculum,
            scheduler=self.scheduler,
            teacher_intel=self.teacher_intel,
            harvest_fn=lambda q: self.manager.collect_and_save(q),
        )

    def harvest(self, task: str, *, teachers: list[str] | None = None) -> dict[str, Any]:
        result = self.manager.collect_and_save(task, teachers=teachers)
        ranking = result.get("ranking") or {}
        self.teacher_intel.record(task, ranking)
        if int(ranking.get("pass_count") or 0) == 0:
            self.gaps.collect_from_ranking(task, ranking)
        return result

    def learn_from_turn(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Optional hook: queue gaps; harvest only when OM_DISTILL_ON_LEARN=1."""
        quality = quality or {}
        gap = self.gaps.collect_from_turn(question, answer, quality)
        score = float(quality.get("score") or 0.0)
        if not self.enabled:
            return {
                "step": 94,
                "skipped": True,
                "reason": "OM_DISTILL_ON_LEARN=0",
                "gap": gap,
                "substeps": self.substep_status(),
            }
        if score < 0.7 or len((question or "").strip()) < 40:
            return {
                "step": 94,
                "skipped": True,
                "reason": "quality_or_length_gate",
                "gap": gap,
            }
        try:
            # Queue for scheduler rather than always blocking
            job = self.scheduler.enqueue(
                question,
                priority=3 if score < 0.5 else 6,
                source="chat_learn",
            )
            return {
                "step": 94,
                "queued": True,
                "job": job,
                "gap": gap,
                "substeps": {"94.12": "enqueued", "94.13": bool(gap)},
            }
        except Exception as exc:
            return {"step": 94, "error": str(exc), "gap": gap}

    def run_continuous_cycle(self, *, max_items: int = 5, domain: str = "software") -> dict[str, Any]:
        return self.loop.run_cycle(max_items=max_items, domain=domain)

    def substep_status(self) -> dict[str, Any]:
        return {
            "94.10_teacher_intelligence": self.teacher_intel.status(),
            "94.11_curriculum_generator": self.curriculum.status(),
            "94.12_harvest_scheduler": self.scheduler.status(),
            "94.13_knowledge_gap_collector": self.gaps.status(),
            "94.14_continuous_loop": self.loop.status(),
        }

    def status(self) -> dict[str, Any]:
        meta = self.manager.state.load_meta()
        return {
            "step": 94,
            "name": "Multi-LLM Teacher Distillation",
            "enabled_on_learn": self.enabled,
            "state": meta,
            "output_root": str(self.manager.state.root),
            "substeps": {
                "94.10": "complete",
                "94.11": "complete",
                "94.12": "complete",
                "94.13": "complete",
                "94.14": "complete",
            },
            "substep_detail": self.substep_status(),
            "honest_limit": (
                "Learns from teacher API outputs you are licensed to use. "
                "Does not extract private model weights. Quality still depends on "
                "teacher answers + OM training compute."
            ),
        }


def build_step94_stack() -> TeacherDistillationIntelligence:
    """Convenience constructor (also available via create_continuous_loop)."""
    _ = create_continuous_loop
    return TeacherDistillationIntelligence()
