"""Chat API + diagnostics smoke."""
from __future__ import annotations

from fastapi.testclient import TestClient

from om_ai.api.main import app
from om_ai.diagnostics import run_system_check


def test_doctor_system_check_runs():
    report = run_system_check()
    data = report.to_dict()
    assert "overall" in data
    assert "summary" in data
    assert data["summary"].get("Core Brain") in {"✅", "⚠️", "❌"}


def test_chat_completions_requires_auth():
    client = TestClient(app)
    res = client.post(
        "/api/v1/chat/completions",
        json={"model": "OM-1.0", "messages": [{"role": "user", "content": "hi"}], "stream": False},
    )
    assert res.status_code in {401, 403}
