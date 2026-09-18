"""Capability-level allow/deny rules."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CapabilityPolicy:
    allowed_capabilities: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
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
            }
        )
    )
    denied_capabilities: frozenset[str] = field(default_factory=frozenset)

    def is_allowed(self, capability: str) -> bool:
        cap = capability.strip()
        if cap in self.denied_capabilities:
            return False
        return cap in self.allowed_capabilities
