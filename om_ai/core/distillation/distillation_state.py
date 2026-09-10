"""Persistent paths and run state for teacher distillation."""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class DistillationState:
    """Tracks harvest runs under data/om_distillation/."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else (_repo_root() / "data" / "om_distillation")
        self.raw_dir = self.root / "raw"
        self.clean_dir = self.root / "clean"
        self.ranked_dir = self.root / "ranked"
        self.sft_dir = self.root / "sft"
        self.dpo_dir = self.root / "dpo"
        self.meta_path = self.root / "state.json"
        for d in (self.raw_dir, self.clean_dir, self.ranked_dir, self.sft_dir, self.dpo_dir):
            d.mkdir(parents=True, exist_ok=True)

    def slug(self, task: str, *, max_len: int = 48) -> str:
        base = re.sub(r"[^a-z0-9]+", "_", (task or "").lower()).strip("_")
        return (base[:max_len] or "task").rstrip("_")

    def new_run_id(self, task: str) -> str:
        return f"{self.slug(task)}_{uuid.uuid4().hex[:8]}"

    def load_meta(self) -> dict[str, Any]:
        if not self.meta_path.is_file():
            return {"runs": 0, "examples_exported": 0, "last_run_id": None}
        try:
            return json.loads(self.meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {"runs": 0, "examples_exported": 0, "last_run_id": None}

    def bump(self, *, run_id: str, exported: int = 0) -> dict[str, Any]:
        meta = self.load_meta()
        meta["runs"] = int(meta.get("runs") or 0) + 1
        meta["examples_exported"] = int(meta.get("examples_exported") or 0) + int(exported)
        meta["last_run_id"] = run_id
        meta["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return meta

    def write_json(self, path: Path, payload: dict[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
