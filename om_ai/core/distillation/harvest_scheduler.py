"""STEP 94.12 — Autonomous Harvest Scheduler.

Queue and run distillation harvest jobs without blocking chat.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable


def _repo_data() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "om_distillation" / "scheduler"


class AutonomousHarvestScheduler:
    """STEP 94.12 — priority queue + batch runner for harvest tasks."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else _repo_data()
        self.root.mkdir(parents=True, exist_ok=True)
        self.queue_path = self.root / "queue.jsonl"
        self.state_path = self.root / "state.json"

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return {"enqueued": 0, "completed": 0, "failed": 0, "last_run_at": None}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {"enqueued": 0, "completed": 0, "failed": 0, "last_run_at": None}

    def _save_state(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def enqueue(
        self,
        question: str,
        *,
        priority: int = 5,
        domain: str = "general",
        source: str = "manual",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q = (question or "").strip()
        if not q:
            raise ValueError("question is required")
        item = {
            "id": f"job_{uuid.uuid4().hex[:10]}",
            "question": q,
            "priority": int(priority),
            "domain": domain,
            "source": source,
            "status": "queued",
            "meta": meta or {},
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with self.queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        state = self._load_state()
        state["enqueued"] = int(state.get("enqueued") or 0) + 1
        self._save_state(state)
        return item

    def enqueue_many(self, questions: list[dict[str, Any] | str], *, source: str = "curriculum") -> list[dict[str, Any]]:
        out = []
        for q in questions or []:
            if isinstance(q, str):
                out.append(self.enqueue(q, source=source))
            else:
                out.append(
                    self.enqueue(
                        str(q.get("question") or ""),
                        priority=int(q.get("priority") or 5),
                        domain=str(q.get("domain") or "general"),
                        source=source,
                        meta={"id": q.get("id"), "level": q.get("level")},
                    )
                )
        return out

    def _read_queue(self) -> list[dict[str, Any]]:
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

    def _write_queue(self, rows: list[dict[str, Any]]) -> None:
        with self.queue_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def pending(self) -> list[dict[str, Any]]:
        rows = [r for r in self._read_queue() if r.get("status") == "queued"]
        rows.sort(key=lambda r: (int(r.get("priority") or 99), str(r.get("created_at") or "")))
        return rows

    def next_batch(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.pending()[: max(1, int(limit))]

    def run_once(
        self,
        harvest_fn: Callable[[str], Any],
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Run up to ``limit`` queued jobs through ``harvest_fn(question)``."""
        batch = self.next_batch(limit)
        results = []
        rows = self._read_queue()
        by_id = {r.get("id"): r for r in rows}
        state = self._load_state()

        for job in batch:
            jid = job.get("id")
            try:
                payload = harvest_fn(str(job.get("question") or ""))
                status = "completed"
                state["completed"] = int(state.get("completed") or 0) + 1
                err = ""
            except Exception as exc:
                payload = None
                status = "failed"
                state["failed"] = int(state.get("failed") or 0) + 1
                err = str(exc)
            if jid in by_id:
                by_id[jid]["status"] = status
                by_id[jid]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                if err:
                    by_id[jid]["error"] = err
            results.append({"id": jid, "status": status, "error": err or None, "result": payload})

        self._write_queue(list(by_id.values()))
        state["last_run_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save_state(state)
        return {
            "step": "94.12",
            "ran": len(results),
            "results": results,
            "pending": len(self.pending()),
            "state": state,
        }

    def status(self) -> dict[str, Any]:
        state = self._load_state()
        return {
            "step": "94.12",
            "name": "Autonomous Harvest Scheduler",
            "pending": len(self.pending()),
            "state": state,
            "queue_path": str(self.queue_path),
        }
