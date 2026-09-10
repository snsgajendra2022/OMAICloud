"""Improvement cycle — orchestrate autonomous OM learning loop."""
from __future__ import annotations

import time
from typing import Any

from .distillation_worker import DistillationWorker
from .learning_scheduler import LearningScheduler
from .training_queue import TrainingQueue


class ImprovementCycle:
    """
    Knowledge Gaps
            |
            ↓
    Learning Scheduler
            |
            ↓
    Distillation Worker (teachers)
            |
            ↓
    Training Queue
            |
            ↓
    OM Improvement ready
    """

    def __init__(
        self,
        *,
        scheduler: LearningScheduler | None = None,
        worker: DistillationWorker | None = None,
        training_queue: TrainingQueue | None = None,
    ) -> None:
        self.scheduler = scheduler or LearningScheduler()
        self.worker = worker or DistillationWorker()
        self.training_queue = training_queue or TrainingQueue()

    def seed_from_gaps(self, *, limit: int = 10) -> dict[str, Any]:
        jobs = self.scheduler.enqueue_from_gaps(limit=limit)
        return {"seeded": len(jobs), "jobs": [j.get("id") for j in jobs]}

    def seed_topic(self, topic: str, *, count: int = 5, domain: str = "software") -> dict[str, Any]:
        jobs = self.scheduler.enqueue_topic(topic, count=count, domain=domain)
        return {"seeded": len(jobs), "topic": topic, "jobs": [j.get("id") for j in jobs]}

    def run_once(self, *, max_items: int = 5, auto_seed_gaps: bool = True) -> dict[str, Any]:
        seeded = None
        if auto_seed_gaps and not self.scheduler.pending():
            seeded = self.seed_from_gaps(limit=max_items)

        batch = self.scheduler.next_batch(max_items)
        results = []
        for job in batch:
            jid = str(job.get("id") or "")
            question = str(job.get("question") or "")
            out = self.worker.run_job(question)
            if out.get("ok"):
                # Prefer nested collect_and_save payload
                payload = out.get("result") if isinstance(out.get("result"), dict) else out
                train_job = self.training_queue.enqueue_from_distill(payload or {})
                self.scheduler.mark(jid, "completed")
                results.append(
                    {
                        "id": jid,
                        "status": "completed",
                        "run_id": out.get("run_id"),
                        "train_job": (train_job or {}).get("id"),
                    }
                )
            else:
                self.scheduler.mark(jid, "failed", error=str(out.get("error") or "failed"))
                results.append({"id": jid, "status": "failed", "error": out.get("error")})

        return {
            "step": "94.15",
            "phase": "improvement_cycle",
            "seeded": seeded,
            "ran": len(results),
            "results": results,
            "pending": self.scheduler.status(),
            "training_queue": self.training_queue.status(),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def start(
        self,
        *,
        max_items: int = 5,
        topic: str | None = None,
        count: int = 5,
        domain: str = "software",
        cycles: int = 1,
        auto_seed_gaps: bool = True,
    ) -> dict[str, Any]:
        """Entry point for ``om-ai learn start``."""
        planned = None
        if topic:
            planned = self.seed_topic(topic, count=count, domain=domain)
            auto_seed_gaps = False

        cycle_reports = []
        for i in range(max(1, int(cycles))):
            cycle_reports.append(
                self.run_once(max_items=max_items, auto_seed_gaps=auto_seed_gaps and i == 0)
            )
            auto_seed_gaps = False

        return {
            "command": "learn.start",
            "planned": planned,
            "cycles": cycle_reports,
            "status": self.status(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "command": "learn",
            "scheduler": self.scheduler.status(),
            "training_queue": self.training_queue.status(),
            "flow": [
                "knowledge_gaps",
                "learning_scheduler",
                "question_generator",
                "ollama_teachers",
                "distillation_engine",
                "sft_dpo_dataset",
                "training_queue",
                "om_improvement",
            ],
        }
