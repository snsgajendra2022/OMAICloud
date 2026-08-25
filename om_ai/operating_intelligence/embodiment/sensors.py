"""Sensor ingest contract (stub)."""
from __future__ import annotations

from typing import Any


SENSOR_KINDS = (
    "camera",
    "microphone",
    "temperature",
    "pressure",
    "motion",
    "gps",
    "light",
    "distance",
    "biometric",
)


def status() -> str:
    return "stub"


def ingest(reading: dict[str, Any]) -> dict[str, Any]:
    kind = str(reading.get("kind") or "unknown")
    return {
        "ok": False,
        "implemented": False,
        "kind": kind,
        "accepted_kinds": list(SENSOR_KINDS),
        "message": "Sensor pipeline not connected. Wire drivers → normalize → decide → act.",
        "reading": reading,
    }
