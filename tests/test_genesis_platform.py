"""Genesis platform adapters: intent, memory layers, tools, coding_brain, enterprise."""
from __future__ import annotations

from om_ai.agents.roles import list_agents, select_agent
from om_ai.coding_brain import catalog, handle
from om_ai.core.intent_engine import classify, route
from om_ai.core.response import check_quality
from om_ai.enterprise import status as enterprise_status
from om_ai.knowledge.corpus import ensure_corpus_layout
from om_ai.memory.layers import LayeredMemory
from om_ai.tools import list_tools, select_tool


def test_intent_react_login():
    c = classify("Create React login page")
    r = route(c)
    assert c.framework == "react"
    assert r["agent"] == "coding"
    assert c.domain == "frontend"


def test_memory_project_layer(tmp_path):
    mem = LayeredMemory(str(tmp_path / "m.sqlite3"))
    mid = mem.remember_project("ECTS", ["FastAPI", "Zoho", "React"], "JWT")
    assert mid
    hits = mem.recall("ECTS", layer="project", k=3)
    assert hits
    assert "FastAPI" in hits[0]["content"]


def test_tools_and_coding_brain():
    assert "terminal" in list_tools()
    assert select_tool("git commit message") == "git"
    cat = catalog()
    assert "Python" in cat["languages"]
    assert "React" in cat["frameworks"]
    out = handle("Add health check", root=".", dry_run=True)
    assert out["plan"]


def test_agents_and_enterprise():
    agents = list_agents()
    assert any(a["name"] == "coding" for a in agents)
    sel = select_agent("security review of auth")
    assert sel["selected"]["name"] in {"security", "coding", "master"}
    st = enterprise_status()
    assert st["features"]["api_keys"] is True


def test_corpus_layout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    info = ensure_corpus_layout(tmp_path)
    assert info["ok"]
    assert (tmp_path / "data" / "om-knowledge-corpus" / "knowledge" / "science" / "raw").is_dir()


def test_quality_gate():
    assert check_quality("Hello, I am OM AI and I can help.")["ok"]
