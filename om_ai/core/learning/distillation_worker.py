"""Distillation worker — run teacher harvest jobs for the learning loop."""
from __future__ import annotations

from typing import Any, Callable


class DistillationWorker:
    """
    Knowledge Gaps / Scheduler jobs
            |
            ↓
    Distillation Engine / TeacherManager
            |
            ↓
    SFT/DPO artifacts
    """

    def __init__(
        self,
        *,
        harvest_fn: Callable[[str], Any] | None = None,
    ) -> None:
        self.harvest_fn = harvest_fn

    def _default_harvest(self, question: str) -> dict[str, Any]:
        from om_ai.core.distillation import create_teacher_manager

        manager = create_teacher_manager()
        return manager.collect_and_save(question)

    def run_job(self, question: str) -> dict[str, Any]:
        q = (question or "").strip()
        if not q:
            return {"ok": False, "error": "empty_question"}
        fn = self.harvest_fn or self._default_harvest
        try:
            result = fn(q)
            return {
                "ok": True,
                "question": q,
                "result": result,
                "run_id": (result or {}).get("run_id") if isinstance(result, dict) else None,
                "exported": ((result or {}).get("export") or {}).get("exported")
                if isinstance(result, dict)
                else 0,
            }
        except Exception as exc:
            return {"ok": False, "question": q, "error": str(exc)}

    def run_batch(self, questions: list[str]) -> dict[str, Any]:
        items = []
        ok = 0
        for q in questions or []:
            item = self.run_job(q)
            items.append(item)
            if item.get("ok"):
                ok += 1
        return {"ok": ok, "failed": len(items) - ok, "items": items}
