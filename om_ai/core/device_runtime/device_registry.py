"""Registered devices / hosts for companion control."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock


@dataclass
class DeviceInfo:
    device_id: str
    platform: str
    label: str = ""
    metadata: dict = field(default_factory=dict)


class DeviceRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._devices: dict[str, DeviceInfo] = {}

    def register(self, device: DeviceInfo) -> None:
        with self._lock:
            self._devices[device.device_id] = device

    def get(self, device_id: str) -> DeviceInfo | None:
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(self) -> list[DeviceInfo]:
        with self._lock:
            return list(self._devices.values())

    def ensure_localhost(self) -> DeviceInfo:
        existing = self.get("local")
        if existing:
            return existing
        import platform as plat

        dev = DeviceInfo(
            device_id="local",
            platform=plat.system().lower(),
            label="Local host",
        )
        self.register(dev)
        return dev
