"""Training queue — stage distilled SFT/DPO examples for OM training."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


def _root() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "om_learning" / "training_queue"


class TrainingQueue:
    """Persist training jobs produced by distillation for later SFT/DPO."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else _root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "queue.jsonl"
        self.buffer = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "om-memory"
            / "advanced_learning"
            / "training_buffer.jsonl"
        )

    def enqueue_from_distill(self, distill_result: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(distill_result, dict):
            return None
        dataset = distill_result.get("dataset") or distill_result
        sft = dataset.get("sft") if isinstance(dataset, dict) else None
        # collect_and_save nests dataset under result
        if not sft and isinstance(distill_result.get("dataset"), dict):
            sft = distill_result["dataset"].get("sft")
        if not sft and distill_result.get("sft"):
            sft = distill_result.get("sft")
        # After collect_and_save, structure is result["dataset"]["sft"]
        if not sft:
            inner = distill_result.get("result") if isinstance(distill_result.get("result"), dict) else {}
            sft = (inner.get("dataset") or {}).get("sft")
        if not sft:
            return None
        job = {
            "id": f"train_{uuid.uuid4().hex[:10]}",
            "type": "sft",
            "status": "queued",
            "run_id": distill_result.get("run_id") or (dataset.get("run_id") if isinstance(dataset, dict) else None),
            "instruction": sft.get("instruction") or sft.get("prompt"),
            "example": sft,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(job, ensure_ascii=False) + "\n")
        # Also append to shared OM training buffer
        self.buffer.parent.mkdir(parents=True, exist_ok=True)
        with self.buffer.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "sft",
                        "messages": sft.get("messages"),
                        "score": (sft.get("meta") or {}).get("score"),
                        "source": "om_learn_queue",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        return job

    def list_jobs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        return rows[-limit:]

    def pending_count(self) -> int:
        return sum(1 for j in self.list_jobs(limit=10000) if j.get("status") == "queued")

    def status(self) -> dict[str, Any]:
        jobs = self.list_jobs(limit=10000)
        return {
            "module": "training_queue",
            "total": len(jobs),
            "queued": sum(1 for j in jobs if j.get("status") == "queued"),
            "path": str(self.path),
            "training_buffer": str(self.buffer),
        }
