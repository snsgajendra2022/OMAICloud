"""Device capability catalog."""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True)
class DeviceCapability:
    name: str
    handler: str
    description: str = ""


class DeviceCapabilityRegistry:
    DEFAULT_CAPABILITIES: tuple[str, ...] = (
        "application.open",
        "application.close",
        "filesystem.list",
        "filesystem.read",
        "filesystem.write",
        "filesystem.move",
        "filesystem.delete",
        "browser.open",
        "browser.navigate",
        "process.list",
        "process.start",
        "process.stop",
        "system.notification",
        "system.volume",
    )

    def __init__(self) -> None:
        self._lock = RLock()
        self._caps: dict[str, DeviceCapability] = {}
        for name in self.DEFAULT_CAPABILITIES:
            self.register(DeviceCapability(name=name, handler=name.replace(".", "_")))

    def register(self, cap: DeviceCapability) -> None:
        with self._lock:
            self._caps[cap.name] = cap

    def get(self, name: str) -> DeviceCapability | None:
        with self._lock:
            return self._caps.get(name)

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._caps.keys())
