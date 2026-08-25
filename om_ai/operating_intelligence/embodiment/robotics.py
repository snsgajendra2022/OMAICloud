"""Robotics control contract (stub — simulate before physical)."""
from __future__ import annotations

from typing import Any


def status() -> str:
    return "stub"


def control(command: dict[str, Any], *, simulate: bool = True) -> dict[str, Any]:
    return {
        "ok": False,
        "implemented": False,
        "simulate": simulate,
        "command": command,
        "capabilities_planned": [
            "navigation",
            "object_detection",
            "voice_control",
            "motion_planning",
            "obstacle_avoidance",
        ],
        "message": "Robotics controller not connected. Use simulation mode first.",
    }
