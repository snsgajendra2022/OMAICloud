"""STEP 94.15 — Learning Scheduler.

Pull knowledge gaps / curriculum topics into a runnable learning queue.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


def _root() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "om_learning" / "scheduler"


class LearningScheduler:
    """Queue background learning jobs for the autonomous loop."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else _root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.queue_path = self.root / "jobs.jsonl"
        self.state_path = self.root / "state.json"

    def _state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return {"enqueued": 0, "completed": 0, "failed": 0, "running": False}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {"enqueued": 0, "completed": 0, "failed": 0, "running": False}

    def _save_state(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def enqueue(
        self,
        question: str,
        *,
        source: str = "manual",
        priority: int = 5,
        domain: str = "software",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q = (question or "").strip()
        if not q:
            raise ValueError("question required")
        job = {
            "id": f"learn_{uuid.uuid4().hex[:10]}",
            "question": q,
            "source": source,
            "priority": int(priority),
            "domain": domain,
            "status": "queued",
            "meta": meta or {},
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with self.queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(job, ensure_ascii=False) + "\n")
        st = self._state()
        st["enqueued"] = int(st.get("enqueued") or 0) + 1
        self._save_state(st)
        return job

    def enqueue_from_gaps(self, *, limit: int = 10) -> list[dict[str, Any]]:
        from om_ai.core.distillation import KnowledgeGapCollector, CurriculumGenerator

        gaps = KnowledgeGapCollector().top_gaps(limit=limit)
        if not gaps:
            return []
        cur = CurriculumGenerator().from_gaps(gaps, per_gap=1)
        out = []
        for q in cur.get("questions") or []:
            out.append(
                self.enqueue(
                    str(q.get("question") or ""),
                    source="gaps",
                    priority=int(q.get("priority") or 5),
                    domain=str(q.get("domain") or "software"),
                    meta={"curriculum_id": cur.get("curriculum_id"), "level": q.get("level")},
                )
            )
        return out

    def enqueue_topic(self, topic: str, *, count: int = 5, domain: str = "software") -> list[dict[str, Any]]:
        from om_ai.core.distillation import CurriculumGenerator

        cur = CurriculumGenerator().generate(topic, domain=domain, count=count)
        out = []
        for q in cur.get("questions") or []:
            out.append(
                self.enqueue(
                    str(q.get("question") or ""),
                    source="topic",
                    priority=int(q.get("priority") or 5),
                    domain=domain,
                    meta={"curriculum_id": cur.get("curriculum_id"), "topic": topic},
                )
            )
        return out

    def _read(self) -> list[dict[str, Any]]:
        if not self.queue_path.is_file():
            return []
        rows = []
        for line in self.queue_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        return rows

    def _write(self, rows: list[dict[str, Any]]) -> None:
        with self.queue_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def pending(self) -> list[dict[str, Any]]:
        rows = [r for r in self._read() if r.get("status") == "queued"]
        rows.sort(key=lambda r: (int(r.get("priority") or 99), str(r.get("created_at") or "")))
        return rows

    def next_batch(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.pending()[: max(1, int(limit))]

    def mark(self, job_id: str, status: str, *, error: str = "") -> None:
        rows = self._read()
        for row in rows:
            if row.get("id") == job_id:
                row["status"] = status
                row["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                if error:
                    row["error"] = error
        self._write(rows)
        st = self._state()
        if status == "completed":
            st["completed"] = int(st.get("completed") or 0) + 1
        elif status == "failed":
            st["failed"] = int(st.get("failed") or 0) + 1
        self._save_state(st)

    def status(self) -> dict[str, Any]:
        st = self._state()
        return {
            "module": "learning_scheduler",
            "pending": len(self.pending()),
            "state": st,
            "path": str(self.queue_path),
        }
