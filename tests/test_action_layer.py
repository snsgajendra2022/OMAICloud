"""STEP 86–88 action / internet / knowledge brain tests."""
from __future__ import annotations

from om_ai.tools.intelligence import (
    AutonomousActionLayer,
    ToolDecisionEngine,
    ActionPermissionGate,
)
from om_ai.knowledge.brain import AdvancedKnowledgeBrain
from om_ai.internet import InternetIntelligence
from om_ai.roadmap import roadmap_status


def test_decision_explain_python_no_tools():
    d = ToolDecisionEngine().decide("Explain Python")
    assert d.needs_tools is False
    assert d.mode == "answer"


def test_decision_weather_needs_web():
    d = ToolDecisionEngine().decide("What is today's weather in Delhi?")
    assert d.needs_tools is True
    assert "web" in d.tools or "knowledge" in d.tools


def test_decision_calculator():
    d = ToolDecisionEngine().decide("What is 15% of 200?")
    assert "calculator" in d.tools


def test_permission_blocks_high_risk_by_default(monkeypatch):
    monkeypatch.setenv("OM_ACTION_ALLOW_HIGH", "0")
    monkeypatch.delenv("OM_SHELL_ENABLED", raising=False)
    v = ActionPermissionGate().check("terminal", "run ls")
    assert v.allowed is False
    assert v.requires_approval is True


def test_action_layer_date(monkeypatch):
    monkeypatch.setenv("OM_ACTION_LAYER", "1")
    monkeypatch.setenv("OM_CHAT_TOOLS", "1")
    out = AutonomousActionLayer().run("What is today's date?")
    assert out.needs_tools is True
    assert "date" in out.tools_planned or "date" in out.tools_allowed
    assert out.execution.get("ok") or out.response_context or out.analysis


def test_action_layer_direct_answer(monkeypatch):
    monkeypatch.setenv("OM_ACTION_LAYER", "1")
    out = AutonomousActionLayer().run("Explain Python")
    assert out.needs_tools is False


def test_internet_blocked_when_live_off(monkeypatch):
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE", "0")
    r = InternetIntelligence().research("latest AI news")
    assert r.ok is False
    assert "OM_LIVE_KNOWLEDGE" in (r.blocked_reason or "")


def test_knowledge_brain_entities():
    brain = AdvancedKnowledgeBrain()
    out = brain.ingest("Laravel uses PHP and requires Composer", source="test")
    assert "laravel" in (out.get("entities") or {}) or "php" in (out.get("entities") or {})


def test_roadmap_86_live():
    status = roadmap_status()
    assert status["86"]["status"] == "live"
    assert status["87"]["status"] == "live"
    assert status["88"]["status"] == "live"
