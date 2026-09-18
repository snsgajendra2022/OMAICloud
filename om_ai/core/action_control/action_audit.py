"""Append-only audit log for actions and approvals."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .action_request import ActionRequest
from .action_result import ActionResult


def _default_audit_path() -> Path:
    return Path("artifacts/companion/actions_audit.jsonl")


class ActionAudit:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else _default_audit_path()
        self._lock = threading.Lock()

    def append(self, event_type: str, payload: dict[str, Any]) -> str:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **payload,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, default=str, ensure_ascii=False)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return record["ts"]

    def log_request(self, request: ActionRequest) -> str:
        return self.append(
            "action_request",
            {
                "action_id": request.action_id,
                "action_type": request.action_type,
                "risk_class": request.risk_class.value,
                "actor": request.actor,
                "source": request.source,
            },
        )

    def log_approval_pending(self, request: ActionRequest) -> str:
        return self.append(
            "approval_pending",
            {"action_id": request.action_id, "action_type": request.action_type},
        )

    def log_approval_decision(
        self, action_id: str, *, approved: bool, approver: str
    ) -> str:
        return self.append(
            "approval_decision",
            {
                "action_id": action_id,
                "approved": approved,
                "approver": approver,
            },
        )

    def log_result(self, result: ActionResult) -> str:
        return self.append(
            "action_result",
            {
                "action_id": result.action_id,
                "status": result.status.value,
                "error": result.error,
            },
        )
