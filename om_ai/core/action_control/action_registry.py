"""Registry of known action types and default risk metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from .action_request import ActionRequest, RiskClass


@dataclass(frozen=True)
class ActionSpec:
    action_type: str
    default_risk: RiskClass
    description: str = ""
    parameter_schema: dict = field(default_factory=dict)


class ActionRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._specs: dict[str, ActionSpec] = {}

    def register(self, spec: ActionSpec) -> None:
        key = spec.action_type.strip()
        with self._lock:
            self._specs[key] = spec

    def get(self, action_type: str) -> ActionSpec | None:
        with self._lock:
            return self._specs.get(action_type.strip())

    def list_types(self) -> list[str]:
        with self._lock:
            return sorted(self._specs.keys())

    def validate_request(self, request: ActionRequest) -> list[str]:
        errors: list[str] = []
        spec = self.get(request.action_type)
        if spec is None:
            errors.append(f"unknown action_type: {request.action_type}")
            return errors
        order = list(RiskClass)
        if order.index(request.risk_class) < order.index(spec.default_risk):
            errors.append(
                f"risk_class {request.risk_class.value} understates registered "
                f"minimum {spec.default_risk.value}"
            )
        required = set(spec.parameter_schema.get("required", []))
        missing = required - set(request.parameters.keys())
        if missing:
            errors.append(f"missing parameters: {sorted(missing)}")
        return errors


def default_action_registry() -> ActionRegistry:
    reg = ActionRegistry()
    builtins = [
        ActionSpec("command.exec", RiskClass.EXTERNAL_SIDE_EFFECT, "Run argv subprocess"),
        ActionSpec("filesystem.read", RiskClass.READ_ONLY),
        ActionSpec("filesystem.write", RiskClass.REVERSIBLE_WRITE),
        ActionSpec("filesystem.delete", RiskClass.DESTRUCTIVE),
        ActionSpec("application.open", RiskClass.EXTERNAL_SIDE_EFFECT),
        ActionSpec("browser.navigate", RiskClass.EXTERNAL_SIDE_EFFECT),
        ActionSpec("process.start", RiskClass.EXTERNAL_SIDE_EFFECT),
        ActionSpec("process.stop", RiskClass.DESTRUCTIVE),
        ActionSpec("system.notification", RiskClass.LOW_IMPACT),
    ]
    for spec in builtins:
        reg.register(spec)
    return reg
