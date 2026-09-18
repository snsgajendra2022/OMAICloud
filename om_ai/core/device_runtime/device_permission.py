"""Device-level permission checks."""
from __future__ import annotations

from dataclasses import dataclass, field

from om_ai.core.companion_security import CapabilityPolicy, SecurityContext


@dataclass
class DevicePermission:
    capability_policy: CapabilityPolicy = field(default_factory=CapabilityPolicy)

    def allow(self, ctx: SecurityContext, capability: str) -> bool:
        if ctx.is_external_content and capability.startswith(
            ("process.", "filesystem.delete")
        ):
            return False
        return self.capability_policy.is_allowed(capability)
