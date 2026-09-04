"""
Action audit log — append-only JSONL for tool decisions and executions.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class ActionAuditLog:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(
            path
            or os.environ.get("OM_ACTION_AUDIT_LOG", "data/om-memory/action_audit.jsonl")
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: dict[str, Any]) -> None:
        row = {
            "ts": time.time(),
            **(event or {}),
        }
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass
