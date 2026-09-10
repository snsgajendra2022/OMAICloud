"""STEP 94.14 — Continuous Distillation Loop.

Gaps → Curriculum → Schedule → Harvest/Distill → Teacher Intelligence update.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from .curriculum_generator import CurriculumGenerator
from .harvest_scheduler import AutonomousHarvestScheduler
from .knowledge_gap_collector import KnowledgeGapCollector
from .teacher_intelligence import TeacherIntelligence


class ContinuousDistillationLoop:
    """STEP 94.14 — autonomous self-improvement data loop for OM distillation."""

    def __init__(
        self,
        *,
        gaps: KnowledgeGapCollector | None = None,
        curriculum: CurriculumGenerator | None = None,
        scheduler: AutonomousHarvestScheduler | None = None,
        teacher_intel: TeacherIntelligence | None = None,
        harvest_fn: Callable[[str], Any] | None = None,
        root: Path | str | None = None,
    ) -> None:
        base = Path(root) if root else None
        self.gaps = gaps or KnowledgeGapCollector(base / "gaps" if base else None)
        self.curriculum = curriculum or CurriculumGenerator(base / "curriculum" if base else None)
        self.scheduler = scheduler or AutonomousHarvestScheduler(base / "scheduler" if base else None)
        self.teacher_intel = teacher_intel or TeacherIntelligence(base / "teacher_intel" if base else None)
        self.harvest_fn = harvest_fn

    def set_harvest_fn(self, fn: Callable[[str], Any]) -> None:
        self.harvest_fn = fn

    def plan_from_gaps(
        self,
        *,
        gap_limit: int = 10,
        per_gap: int = 2,
        domain: str = "software",
    ) -> dict[str, Any]:
        top = self.gaps.top_gaps(limit=gap_limit)
        cur = self.curriculum.from_gaps(top, per_gap=per_gap, domain=domain)
        jobs = self.scheduler.enqueue_many(cur.get("questions") or [], source="94.14_gaps")
        return {
            "step": "94.14",
            "phase": "plan",
            "gaps_used": len(top),
            "curriculum_id": cur.get("curriculum_id"),
            "queued": len(jobs),
            "curriculum_path": cur.get("path"),
        }

    def plan_topic(
        self,
        topic: str,
        *,
        domain: str = "software",
        count: int = 8,
    ) -> dict[str, Any]:
        cur = self.curriculum.generate(topic, domain=domain, count=count)
        jobs = self.scheduler.enqueue_many(cur.get("questions") or [], source="94.14_topic")
        return {
            "step": "94.14",
            "phase": "plan_topic",
            "topic": topic,
            "curriculum_id": cur.get("curriculum_id"),
            "queued": len(jobs),
            "curriculum_path": cur.get("path"),
        }

    def run_cycle(
        self,
        *,
        max_items: int = 5,
        auto_plan_gaps: bool = True,
        domain: str = "software",
    ) -> dict[str, Any]:
        """One continuous loop tick."""
        planned = None
        if auto_plan_gaps and not self.scheduler.pending():
            if self.gaps.top_gaps(limit=1):
                planned = self.plan_from_gaps(domain=domain)

        if self.harvest_fn is None:
            return {
                "step": "94.14",
                "phase": "idle",
                "error": "harvest_fn_not_configured",
                "planned": planned,
                "pending": self.scheduler.status(),
            }

        def _harvest(question: str) -> Any:
            result = self.harvest_fn(question)
            # Update teacher intelligence when ranking is present
            if isinstance(result, dict):
                ranking = result.get("ranking") or {}
                if ranking:
                    self.teacher_intel.record(question, ranking)
                # If harvest failed quality, register gap
                if ranking and int(ranking.get("pass_count") or 0) == 0:
                    self.gaps.collect_from_ranking(question, ranking)
            return result

        ran = self.scheduler.run_once(_harvest, limit=max_items)
        return {
            "step": "94.14",
            "phase": "cycle",
            "planned": planned,
            "harvest": ran,
            "teacher_intel": self.teacher_intel.status(),
            "gaps": self.gaps.status(),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def status(self) -> dict[str, Any]:
        return {
            "step": "94.14",
            "name": "Continuous Distillation Loop",
            "teacher_intelligence": self.teacher_intel.status(),
            "curriculum": self.curriculum.status(),
            "scheduler": self.scheduler.status(),
            "gaps": self.gaps.status(),
            "harvest_fn_ready": self.harvest_fn is not None,
        }
