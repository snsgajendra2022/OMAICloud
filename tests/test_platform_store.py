"""Platform store + API smoke tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from om_ai.api.platform_store import PlatformStore


def test_platform_store_crud(tmp_path):
    store = PlatformStore(str(tmp_path / "plat.sqlite3"))
    ws = store.create_workspace("t", "user:1", name="Team")
    assert ws["name"] == "Team"
    f = store.create_file("t", "user:1", name="a.txt", content_text="hello")
    assert f["name"] == "a.txt"
    p = store.create_prompt("t", "user:1", name="Greet", content="Say hi")
    assert p["version"] == 1
    m = store.create_memory("t", "user:1", content="Name is Gajendra")
    assert "Gajendra" in m["content"]
    results = store.search_all("t", "user:1", "Gajendra")
    assert results["memories"]
    explore = store.list_explore()
    assert len(explore) >= 4


def test_platform_routes_require_auth():
    from om_ai.api.main import app

    client = TestClient(app)
    r = client.get("/v1/files")
    assert r.status_code in {401, 403}
