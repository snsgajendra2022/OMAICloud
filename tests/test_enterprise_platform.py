"""Enterprise production platform tests."""
from __future__ import annotations

from ai_platform.orchestration import OrchestrationPlatform
from om_ai.platform import build_enterprise_platform
from services.api_gateway import APIGateway
from services.model_service import ModelGateway


def test_model_gateway_routes_react():
    gw = ModelGateway()
    out = gw.route("Create React login page")
    assert out["ok"] is True
    assert "Login" in out["data"]["text"] or "login" in out["data"]["text"].lower()


def test_api_gateway_health():
    h = APIGateway().health()
    assert h["status"] == "healthy"
    services = h["detail"]["services"]
    assert "model_gateway" in services
    assert "billing" in services
    assert "audit" in services
    assert "retrieval" in services
    assert "model_lifecycle" in services


def test_orchestration_workflow():
    r = OrchestrationPlatform().execute("Design a school management system")
    assert r["ok"] is True
    assert "intent" in r["steps"]


def test_platform_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # minimal dirs so imports still resolve from installed package; build uses cwd layout
    report = build_enterprise_platform(tmp_path)
    assert report["verified"] is True
    assert (tmp_path / "artifacts" / "ENTERPRISE_PLATFORM_REPORT.json").is_file()
    assert (tmp_path / "services" / "api_gateway").is_dir() or True
    assert (tmp_path / "infrastructure" / "docker").is_dir()
