"""Dispatch device capabilities through controllers."""
from __future__ import annotations

from typing import Any

from om_ai.core.action_control import ActionRequest, RiskClass
from om_ai.core.companion_security import SecurityContext, SecurityRuntime

from .app_controller import AppController
from .browser_controller import BrowserController
from .capability_registry import DeviceCapabilityRegistry
from .device_permission import DevicePermission
from .device_registry import DeviceRegistry
from .file_controller import FileController
from .process_controller import ProcessController
from .system_controller import SystemController


class DeviceRuntime:
    def __init__(
        self,
        *,
        security: SecurityRuntime | None = None,
        device_registry: DeviceRegistry | None = None,
    ) -> None:
        self.security = security or SecurityRuntime()
        self.devices = device_registry or DeviceRegistry()
        self.devices.ensure_localhost()
        self.capabilities = DeviceCapabilityRegistry()
        self.permissions = DevicePermission()
        self.files = FileController(self.security.policy.sandbox_policy)
        self.apps = AppController()
        self.browser = BrowserController()
        self.processes = ProcessController()
        self.system = SystemController()

    def invoke(
        self, ctx: SecurityContext, capability: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if not self.permissions.allow(ctx, capability):
            raise PermissionError(f"capability denied: {capability}")

        request = ActionRequest(
            action_type=capability,
            risk_class=_risk_for_capability(capability),
            parameters=params,
            actor=ctx.actor,
            source="external" if ctx.is_external_content else "internal",
        )
        ok, reason = self.security.guard_action(ctx, request)
        if not ok:
            raise PermissionError(reason)

        handler = getattr(self, f"_handle_{capability.replace('.', '_')}", None)
        if handler is None:
            raise ValueError(f"no handler for {capability}")
        return handler(params)

    def _handle_application_open(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.apps.open_application(
            str(params["app"]), list(params.get("args") or [])
        )

    def _handle_application_close(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.apps.close_application(str(params["app"]))

    def _handle_filesystem_list(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.files.list_dir(params.get("path", "."))

    def _handle_filesystem_read(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.files.read_text(str(params["path"]))

    def _handle_filesystem_write(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.files.write_text(str(params["path"]), str(params.get("content", "")))

    def _handle_filesystem_move(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.files.move(str(params["src"]), str(params["dest"]))

    def _handle_filesystem_delete(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.files.delete(str(params["path"]))

    def _handle_browser_open(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.browser.open_url(str(params["url"]))

    def _handle_browser_navigate(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.browser.navigate(
            str(params["url"]), browser=params.get("browser")
        )

    def _handle_process_list(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.processes.list_processes(limit=int(params.get("limit", 50)))

    def _handle_process_start(self, params: dict[str, Any]) -> dict[str, Any]:
        argv = params.get("argv")
        if not isinstance(argv, list):
            raise TypeError("process.start requires argv list")
        return self.processes.start([str(x) for x in argv])

    def _handle_process_stop(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.processes.stop(int(params["pid"]))

    def _handle_system_notification(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.system.notification(
            str(params.get("title", "OM AI")),
            str(params.get("message", "")),
        )


def _risk_for_capability(capability: str) -> RiskClass:
    if capability.startswith("filesystem.read") or capability.endswith(".list"):
        return RiskClass.READ_ONLY
    if capability == "system.notification":
        return RiskClass.LOW_IMPACT
    if capability.startswith("filesystem."):
        if "delete" in capability:
            return RiskClass.DESTRUCTIVE
        return RiskClass.REVERSIBLE_WRITE
    if capability.startswith("process.stop"):
        return RiskClass.DESTRUCTIVE
    return RiskClass.EXTERNAL_SIDE_EFFECT
