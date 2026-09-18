"""Security audit logging with secret redaction."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .output_validator import OutputValidator


class SecurityAuditLogger:
    def __init__(
        self,
        path: Path | str | None = None,
        *,
        output_validator: OutputValidator | None = None,
    ) -> None:
        self.path = Path(path or "artifacts/companion/security_audit.jsonl")
        self.output = output_validator or OutputValidator()
        self._lock = threading.Lock()

    def log(self, event: str, payload: dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **self.output.sanitize_for_log(payload),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, default=str, ensure_ascii=False)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
