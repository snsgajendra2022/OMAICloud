"""Audit service — append-only enterprise audit trail."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from services._common import ServiceHealth, ok


class AuditService:
    def __init__(self, path: str = "artifacts/enterprise/audit.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def health(self) -> dict[str, Any]:
        return ServiceHealth("audit-service").to_dict()

    def log(self, action: str, *, actor: str = "", tenant_id: str = "default", meta: dict | None = None) -> dict[str, Any]:
        row = {
            "ts": time.time(),
            "action": action,
            "actor": actor,
            "tenant_id": tenant_id,
            "meta": meta or {},
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        # also mirror to om security audit if available
        try:
            from om_ai.security.audit import AuditLog

            AuditLog().record(
                tenant_id=tenant_id,
                actor=actor or "system",
                action=action,
                resource="api-gateway",
                detail=meta or {},
            )
        except Exception:
            pass
        return ok(row)

    def recent(self, limit: int = 50) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        return ok(rows[-limit:])
