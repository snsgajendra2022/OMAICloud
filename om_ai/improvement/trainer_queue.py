"""Queue future SFT/DPO jobs from improvement examples."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


QUEUE_PATH = Path("artifacts/improvement/trainer_queue.jsonl")


def enqueue(
    *,
    sft_path: str,
    preference_path: str = "",
    reason: str = "",
    queue_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(queue_path or QUEUE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    job = {
        "id": str(uuid.uuid4()),
        "ts": time.time(),
        "status": "queued",
        "reason": reason,
        "sft_path": sft_path,
        "preference_path": preference_path,
        "commands": {
            "sft": (
                "om-ai sft --config configs/omai-20m.json "
                "--tokenizer artifacts/tokenizer-production-65536.json "
                f"--checkpoint <base.pt> --data {sft_path} "
                "--output artifacts/checkpoints/om-improve-sft --steps 300 --device mps"
            ),
            "dpo": (
                "om-ai dpo --config configs/omai-20m.json "
                "--tokenizer artifacts/tokenizer-production-65536.json "
                f"--checkpoint <sft.pt> --data {preference_path or sft_path} "
                "--output artifacts/checkpoints/om-improve-dpo --steps 200 --device mps"
            ),
            "eval": "om-ai evaluate run",
        },
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False) + "\n")
    return job


def list_jobs(queue_path: str | Path | None = None, limit: int = 20) -> list[dict[str, Any]]:
    path = Path(queue_path or QUEUE_PATH)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-limit:]
