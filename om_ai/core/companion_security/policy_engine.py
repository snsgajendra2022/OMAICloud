"""Combine capability, sandbox, and boundary policies."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .capability_policy import CapabilityPolicy
from .sandbox_policy import SandboxPolicy
from .security_context import SecurityContext


@dataclass
class PolicyEngine:
    capability_policy: CapabilityPolicy = field(default_factory=CapabilityPolicy)
    sandbox_policy: SandboxPolicy = field(default_factory=SandboxPolicy)

    def evaluate_capability(
        self, ctx: SecurityContext, capability: str
    ) -> tuple[bool, str]:
        if ctx.is_external_content and capability.startswith("system."):
            return False, "external content cannot invoke system capabilities"
        if not self.capability_policy.is_allowed(capability):
            return False, f"capability denied: {capability}"
        return True, ""

    def evaluate_path(self, path: Path | str) -> tuple[bool, str]:
        if self.sandbox_policy.is_path_allowed(path):
            return True, ""
        return False, "path outside allowed roots"
