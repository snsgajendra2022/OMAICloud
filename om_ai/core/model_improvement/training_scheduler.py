"""STEP 28 — Training scheduler."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class TrainingScheduler:
    def next_run(self, *, hours: float = 24.0) -> dict[str, Any]:
        now = datetime.utcnow()
        when = now + timedelta(hours=hours)
        return {
            "scheduled_at": when.isoformat(),
            "created_at": now.isoformat(),
            "hours": hours,
            "status": "scheduled",
        }

    def plan(self, curriculum: dict[str, Any] | None = None) -> dict[str, Any]:
        lessons = list((curriculum or {}).get("lessons") or [])
        return {
            "jobs": [
                {"track": l.get("track"), "examples": l.get("examples"), "status": "queued"}
                for l in lessons
            ],
            "schedule": self.next_run(),
        }
