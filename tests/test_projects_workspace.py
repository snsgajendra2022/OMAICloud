"""Project workspace store + nested API smoke tests."""
from __future__ import annotations

import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from om_ai.api import deps
from om_ai.api.platform_store import PlatformStore
from om_ai.api.workspace_routes import router as workspace_router
from om_ai.api.workspace_store import WorkspaceStore
from om_ai.security.auth import TenantContext


def _client(tmp_path: str):
    import om_ai.api.workspace_store as ws
    import om_ai.api.platform_store as ps

    ws._store = WorkspaceStore(tmp_path)
    ps._store = PlatformStore(tmp_path)

    app = FastAPI()
    app.include_router(workspace_router)

    def fake_auth():
        return TenantContext(tenant_id="t1", actor="user:u1", role="admin")

    app.dependency_overrides[deps.require_auth] = fake_auth
    return TestClient(app)


def test_project_crud_and_nested():
    db = tempfile.mktemp(suffix=".sqlite3")
    client = _client(db)
    r = client.post(
        "/v1/projects",
        json={
            "name": "OM Dating App",
            "description": "Dating product",
            "instructions": "You are a dating product assistant.",
            "model": "OM-1.0",
        },
    )
    assert r.status_code == 201, r.text
    proj = r.json()
    pid = proj["id"]

    r = client.get("/api/projects")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json()["projects"])

    r = client.put(f"/v1/projects/{pid}", json={"favorite": True})
    assert r.status_code == 200
    assert r.json().get("favorite") in (1, True)

    r = client.post(
        f"/api/projects/{pid}/files",
        json={"name": "notes.txt", "content": "Uses React and Node.js", "mime": "text/plain"},
    )
    assert r.status_code == 201

    r = client.get(f"/v1/projects/{pid}/files")
    assert r.status_code == 200
    assert len(r.json()["files"]) == 1

    r = client.post(
        f"/api/projects/{pid}/memory", json={"content": "Database PostgreSQL"}
    )
    assert r.status_code == 201
    r = client.get(f"/api/projects/{pid}/memory")
    assert r.status_code == 200
    assert any("PostgreSQL" in m["content"] for m in r.json()["memories"])

    r = client.post(
        f"/api/projects/{pid}/knowledge",
        json={"name": "API docs", "source_type": "url", "uri": "https://example.com"},
    )
    assert r.status_code == 201

    r = client.get(f"/v1/projects/{pid}")
    assert r.status_code == 200
    body = r.json()
    assert body["file_count"] >= 1
    assert body["memory_count"] >= 1
    assert body["knowledge_count"] >= 1

    r = client.delete(f"/api/projects/{pid}")
    assert r.status_code == 200
