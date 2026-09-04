"""Connectivity bridge — orphan packages wired into chat (nothing deleted)."""
from __future__ import annotations

from om_ai.runtime.connectivity_bridge import enrich_chat_turn, connectivity_status


REQUIRED = [
    "perception",
    "action",
    "actions",
    "autonomous",
    "autonomy",
    "robotics",
    "universal_robotics",
    "hardware",
    "hardware_design",
    "device_control",
    "digital_twin",
    "physical_reasoning",
    "workflow",
    "workflow_memory",
    "software_agent",
    "code_intelligence",
    "decision",
    "goals",
    "legacy",
    "core.memory",
    "core.learning",
    "core.agents",
    "knowledge_graph",
    "rag",
]


def test_all_orphans_connected():
    out = enrich_chat_turn(
        "Build ecommerce website with Python",
        intent={"intent": "code_creation"},
    )
    assert out.get("enabled") is True
    connected = set(out.get("connected") or [])
    missing = [p for p in REQUIRED if p not in connected]
    assert not missing, f"not connected: {missing} failures={[k for k,v in out['modules'].items() if not v.get('ok')]}"


def test_connectivity_status_imports():
    st = connectivity_status()
    assert st.get("connect_all") is True
    for group, rows in (st.get("groups") or {}).items():
        assert rows, group
        assert any(r.get("importable") for r in rows), group


def test_chat_pipeline_has_connectivity_stage():
    from om_ai.runtime.chat_pipeline import run_chat_pipeline

    out = run_chat_pipeline("Explain FastAPI briefly for a project plan")
    assert "tool_decision" in (out.get("stages") or []) or "system_connectivity" in (
        out.get("stages") or []
    )
    # Social/calc may skip connectivity; substantive asks should still sanitize
    ans = out.get("answer") or ""
    assert "Knowledge Brain" not in ans
    assert "[decision]" not in ans
