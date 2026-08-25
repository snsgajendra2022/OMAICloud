"""Digital twin contract (stub)."""
from __future__ import annotations

from typing import Any


def status() -> str:
    return "stub"


def snapshot(twin_id: str) -> dict[str, Any]:
    return {
        "ok": False,
        "implemented": False,
        "twin_id": twin_id,
        "message": "Digital twin store not implemented. Plan: sync real-world state → model → predict → act.",
    }


def update(twin_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "implemented": False,
        "twin_id": twin_id,
        "state": state,
        "message": "Digital twin updates are stubbed.",
    }
