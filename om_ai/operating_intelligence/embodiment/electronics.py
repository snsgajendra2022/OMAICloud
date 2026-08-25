"""Electronics / MCU / IoT control contract (stub)."""
from __future__ import annotations

from typing import Any


SUPPORTED_PROFILES = ("arduino", "esp32", "raspberry-pi", "stm32", "jetson", "plc")
TRANSPORTS = ("mqtt", "serial", "wifi", "bluetooth", "can", "usb", "ethernet")


def status() -> str:
    return "stub"


def command(payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    """Send a hardware command. Default dry_run=True — never actuates in stub mode."""
    return {
        "ok": False,
        "implemented": False,
        "dry_run": dry_run,
        "payload": payload,
        "supported_profiles": list(SUPPORTED_PROFILES),
        "transports": list(TRANSPORTS),
        "message": "Hardware control not connected. Implement gateway drivers before enabling actuators.",
    }
