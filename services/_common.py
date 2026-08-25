"""Shared service contracts for OM enterprise microservices."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceHealth:
    service: str
    status: str = "healthy"
    version: str = "1.0"
    detail: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "status": self.status,
            "version": self.version,
            "om_version": "1.0",
            "detail": self.detail,
            "ts": self.ts,
        }


@dataclass
class ServiceRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    user_id: str = "default"
    payload: dict[str, Any] = field(default_factory=dict)


def ok(data: Any = None, **extra: Any) -> dict[str, Any]:
    out = {"ok": True, "data": data}
    out.update(extra)
    return out


def err(message: str, **extra: Any) -> dict[str, Any]:
    out = {"ok": False, "error": message}
    out.update(extra)
    return out
