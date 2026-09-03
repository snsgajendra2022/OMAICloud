"""OM Security file-backed audit logger (JSON).

SQLite append-only history lives in ``om_ai.security.audit.AuditLog``.
This module is the JSON trail used by the security controller alongside it.
``AuditLog`` / ``AuditEntry`` are re-exported so both APIs can be imported
from this module without dropping either store.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import AuditEntry, AuditLog


class AuditLogEvent:
    """One JSON audit row, with ``to_dict()`` for scripts and tests."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = dict(data or {})

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __repr__(self) -> str:
        return f"AuditLogEvent({self._data!r})"


class AuditLogger:

    def __init__(
        self,
        path="data/om-security/audit.json",
    ):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return []
        if isinstance(raw, list):
            return [row for row in raw if isinstance(row, dict)]
        if isinstance(raw, dict):
            return [raw]
        return []

    def log(self, event: dict) -> bool:
        events = self._load()
        row = dict(event or {})
        row["time"] = datetime.now(timezone.utc).isoformat()
        events.append(row)
        self.path.write_text(
            json.dumps(
                events,
                indent=2,
            )
        )
        return True

    def query(
        self,
        tenant_id: str = "default",
        *,
        limit: int = 100,
        action_filter: str | None = None,
        actor_filter: str | None = None,
    ) -> list[AuditLogEvent]:
        """Newest-first slice of the JSON audit file."""
        rows: list[AuditLogEvent] = []
        for row in reversed(self._load()):
            if str(row.get("tenant_id") or "default") != str(tenant_id):
                continue
            if action_filter and str(row.get("action") or "") != action_filter:
                continue
            if actor_filter and str(row.get("actor") or "") != actor_filter:
                continue
            rows.append(AuditLogEvent(row))
            if len(rows) >= max(1, int(limit)):
                break
        return rows


__all__ = [
    "AuditLogger",
    "AuditLogEvent",
    "AuditLog",
    "AuditEntry",
]
