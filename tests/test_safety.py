"""Safety stack smoke tests."""
from __future__ import annotations

from om_ai.safety.risk import RiskAnalyzer
from om_ai.safety.policy import PolicyEngine
from om_ai.security.audit import AuditLog
from om_ai.security.sandbox import SandboxRunner


def test_risk_and_policy():
    risk = RiskAnalyzer()
    policy = PolicyEngine()
    assert risk is not None
    assert policy is not None


def test_sandbox_and_audit(tmp_path):
    sb = SandboxRunner()
    result = sb.execute(lambda: "ok")
    assert result.get("success") is True

    log = AuditLog(db_path=tmp_path / "audit.sqlite3")
    eid = log.record(
        tenant_id="default",
        actor="test",
        action="test.action",
        resource="unit",
        detail={"ok": True},
    )
    assert eid
    assert log.count("default") >= 1
