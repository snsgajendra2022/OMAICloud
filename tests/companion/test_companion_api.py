"""Companion API route smoke tests (FastAPI TestClient)."""
import pytest

from om_ai.core.companion_runtime import reset_companion_runtime


@pytest.fixture(autouse=True)
def _reset():
    reset_companion_runtime()
    yield
    reset_companion_runtime()


def test_companion_status_and_message():
    from fastapi.testclient import TestClient
    from om_ai.api.main import app

    client = TestClient(app)
    st = client.get("/api/companion/status")
    assert st.status_code == 200
    body = st.json()
    assert "started" in body or "ok" in body or "components" in body or "wake_word" in str(body).lower()

    sess = client.post("/api/companion/session")
    assert sess.status_code == 200
    assert "session_id" in sess.json()

    msg = client.post("/api/companion/message", json={"text": "hello"})
    assert msg.status_code == 200
    data = msg.json()
    assert data.get("answer") or data.get("ok") is not False

    mute = client.post("/api/companion/mute")
    assert mute.status_code == 200
    unmute = client.post("/api/companion/unmute")
    assert unmute.status_code == 200
    interrupt = client.post("/api/companion/interrupt")
    assert interrupt.status_code == 200


def test_companion_devices_endpoint():
    from fastapi.testclient import TestClient
    from om_ai.api.main import app

    client = TestClient(app)
    r = client.get("/api/companion/devices")
    assert r.status_code == 200
