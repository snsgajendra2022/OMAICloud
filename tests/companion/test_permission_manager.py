"""Permission manager tests."""
from om_ai.core.action_control.action_request import ActionRequest, RiskClass
from om_ai.core.action_control.permission import Permission, PermissionDecision
from om_ai.core.action_control.permission_manager import PermissionManager


def test_default_denies_without_grant():
    pm = PermissionManager(allow_everything_forever=False)
    req = ActionRequest(
        action_type="filesystem.write",
        risk_class=RiskClass.REVERSIBLE_WRITE,
        actor="user",
        source="internal",
    )
    assert pm.check(req) in {
        PermissionDecision.DENY,
        PermissionDecision.NEEDS_APPROVAL,
    }


def test_destructive_needs_approval():
    pm = PermissionManager()
    req = ActionRequest(
        action_type="filesystem.delete",
        risk_class=RiskClass.DESTRUCTIVE,
        actor="user",
        source="internal",
    )
    assert pm.check(req) == PermissionDecision.NEEDS_APPROVAL


def test_read_only_auto_allow():
    pm = PermissionManager()
    req = ActionRequest(
        action_type="filesystem.read",
        risk_class=RiskClass.READ_ONLY,
        actor="user",
        source="internal",
        requires_explicit_approval=False,
    )
    assert pm.check(req) == PermissionDecision.ALLOW


def test_scoped_grant_and_revoke():
    pm = PermissionManager()
    pm.grant(
        Permission(
            subject="user",
            action_type="application.open",
            risk_class=RiskClass.EXTERNAL_SIDE_EFFECT,
            decision=PermissionDecision.ALLOW,
        )
    )
    req = ActionRequest(
        action_type="application.open",
        risk_class=RiskClass.EXTERNAL_SIDE_EFFECT,
        actor="user",
        source="internal",
        requires_explicit_approval=True,
    )
    assert pm.check(req) == PermissionDecision.ALLOW
    pm.revoke_subject("user")
    assert pm.check(req) != PermissionDecision.ALLOW


def test_allow_everything_forever_not_default():
    pm = PermissionManager()
    assert pm.allow_everything_forever is False
