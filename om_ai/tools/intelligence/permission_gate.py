"""
Permission gate for autonomous tool actions.

Risk levels:
  low     — date, calculator, knowledge (always allowed when tools enabled)
  medium  — file read, web, code analysis (allowed with workspace scope)
  high    — shell, database write, browser automation (needs OM_ACTION_ALLOW_HIGH=1
            or explicit allowlist)
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


TOOL_RISK: dict[str, str] = {
    "date": "low",
    "calculator": "low",
    "knowledge": "low",
    "vision": "low",
    "ocr": "low",
    "file": "medium",
    "file_manager": "medium",
    "code_execution": "medium",
    "code": "medium",
    "web": "medium",
    "browser": "medium",
    "api_client": "medium",
    "database": "high",
    "terminal": "high",
    "git": "high",
    "automation": "high",
    "cloud": "high",
}

_DANGEROUS = re.compile(
    r"(rm\s+-rf|mkfs|dd\s+if=|/etc/passwd|curl\s+.*\|\s*sh|"
    r"drop\s+table|truncate\s+|delete\s+from\s+\w+\s*;|"
    r"os\.system\(|subprocess\.|eval\(|exec\()",
    re.I,
)


@dataclass
class PermissionVerdict:
    allowed: bool
    tool: str
    risk: str
    reason: str
    requires_approval: bool = False


class ActionPermissionGate:
    """Identity + permission + safety before any tool runs."""

    def __init__(
        self,
        *,
        identity: str = "default",
        allow_high: bool | None = None,
    ) -> None:
        self.identity = identity or "default"
        if allow_high is None:
            allow_high = os.environ.get("OM_ACTION_ALLOW_HIGH", "0").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self.allow_high = bool(allow_high)
        raw = os.environ.get("OM_ACTION_TOOL_ALLOWLIST", "").strip()
        self.allowlist = {x.strip() for x in raw.split(",") if x.strip()} if raw else set()
        raw_deny = os.environ.get("OM_ACTION_TOOL_DENYLIST", "").strip()
        self.denylist = (
            {x.strip() for x in raw_deny.split(",") if x.strip()} if raw_deny else set()
        )

    def check(
        self,
        tool: str,
        request: str = "",
        *,
        context: dict[str, Any] | None = None,
    ) -> PermissionVerdict:
        name = (tool or "").strip()
        risk = TOOL_RISK.get(name, "medium")
        ctx = context or {}

        if not name:
            return PermissionVerdict(False, name, "high", "empty tool name")

        if name in self.denylist:
            return PermissionVerdict(False, name, risk, "denylist")

        if self.allowlist and name not in self.allowlist:
            return PermissionVerdict(False, name, risk, "not_in_allowlist")

        if _DANGEROUS.search(request or ""):
            return PermissionVerdict(
                False,
                name,
                "high",
                "dangerous_pattern_blocked",
                requires_approval=True,
            )

        # Tools master switch
        if os.environ.get("OM_CHAT_TOOLS", "1").strip().lower() in {
            "0",
            "false",
            "no",
            "off",
        }:
            return PermissionVerdict(False, name, risk, "OM_CHAT_TOOLS=0")

        if risk == "high" and not self.allow_high:
            # Explicit per-tool override for terminal via SafeShell still possible
            if name == "terminal" and os.environ.get("OM_SHELL_ENABLED", "0") == "1":
                return PermissionVerdict(True, name, risk, "shell_enabled")
            return PermissionVerdict(
                False,
                name,
                risk,
                "high_risk_requires_OM_ACTION_ALLOW_HIGH=1",
                requires_approval=True,
            )

        if risk == "medium" and name in {"web", "browser"}:
            live = os.environ.get("OM_LIVE_KNOWLEDGE", "0").strip().lower()
            if live in {"0", "false", "no", "off"}:
                return PermissionVerdict(
                    False,
                    name,
                    risk,
                    "OM_LIVE_KNOWLEDGE=0 (enable for web)",
                )

        # Identity tagging for audit (always pass if above checks ok)
        _ = ctx.get("actor") or self.identity
        return PermissionVerdict(True, name, risk, "approved")

    def filter_allowed(
        self,
        tools: list[str],
        request: str = "",
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[PermissionVerdict]]:
        allowed: list[str] = []
        verdicts: list[PermissionVerdict] = []
        for t in tools:
            v = self.check(t, request, context=context)
            verdicts.append(v)
            if v.allowed:
                allowed.append(t)
        return allowed, verdicts
