"""Critical startup / diagnostics / model / chat wiring tests."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_static_ui_files_exist():
    static = ROOT / "om_ai" / "api" / "static"
    for name in ("chat.html", "login.html", "register.html"):
        assert (static / name).is_file(), name


def test_fastapi_app_imports():
    from om_ai.api.main import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/health" in paths
    assert "/login" in paths
    assert "/chat" in paths


def test_health_payload_shape():
    from fastapi.testclient import TestClient
    from om_ai.api.main import app

    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") in {"healthy", "degraded"}
    assert "brain" in body
    assert "memory" in body
    assert "model" in body
    assert "agents" in body
