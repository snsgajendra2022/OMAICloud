"""Action registry validation tests."""
from om_ai.core.action_control.action_registry import (
    ActionRegistry,
    ActionSpec,
    default_action_registry,
)
from om_ai.core.action_control.action_request import ActionRequest, RiskClass


def test_default_registry_has_core_actions():
    reg = default_action_registry()
    types = reg.list_types()
    assert "filesystem.delete" in types
    assert "application.open" in types
    assert "command.exec" in types


def test_unknown_action_rejected():
    reg = default_action_registry()
    req = ActionRequest(
        action_type="shell.rm_rf",
        risk_class=RiskClass.DESTRUCTIVE,
    )
    errors = reg.validate_request(req)
    assert errors


def test_understated_risk_rejected():
    reg = ActionRegistry()
    reg.register(
        ActionSpec("filesystem.delete", RiskClass.DESTRUCTIVE, parameter_schema={})
    )
    req = ActionRequest(
        action_type="filesystem.delete",
        risk_class=RiskClass.READ_ONLY,
    )
    errors = reg.validate_request(req)
    assert any("risk" in e.lower() or "understate" in e.lower() for e in errors)


def test_missing_required_params():
    reg = ActionRegistry()
    reg.register(
        ActionSpec(
            "filesystem.read",
            RiskClass.READ_ONLY,
            parameter_schema={"required": ["path"]},
        )
    )
    req = ActionRequest(action_type="filesystem.read", risk_class=RiskClass.READ_ONLY)
    errors = reg.validate_request(req)
    assert any("missing" in e.lower() for e in errors)
