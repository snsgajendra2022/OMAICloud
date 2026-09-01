"""User-facing formatter vs internal pipeline dump."""
from __future__ import annotations

from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain
from om_ai.core.response.response_formatter import ResponseFormatter
from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
from om_ai.knowledge.context_filter import KnowledgeContextFilter
from om_ai.understanding.query_kind import query_kind


def test_user_response_hides_internal_pipeline():
    brain = OMCognitiveBrain()
    result = brain.process("create react native login and dashboard app")
    user = (result.get("user_response") or result.get("answer") or "").lower()
    assert "react native" in user
    assert "login" in user
    assert "agents:" not in user
    assert "self-critique" not in user
    assert "intent:" not in user
    assert "## evaluation" not in user
    assert "## analysis" not in user
    assert "## understanding" not in user


def test_developer_response_keeps_internal_pipeline():
    result = run_reasoning_pipeline(
        "create react native login and dashboard app",
        retrieve=False,
    )
    dev = (result.get("developer_response") or result.get("markdown") or "").lower()
    assert "## understanding" in dev
    assert "## analysis" in dev
    assert "## evaluation" in dev
    user = (result.get("user_response") or "").lower()
    assert "agents:" not in user
    assert "self-critique" not in user
    assert "react native" in user
    assert "answer" in result
    assert "debug" in result
    assert result["debug"]["intent"]["intent"] in {"coding", "architecture", "debug"}


def test_formatter_direct_payload():
    fmt = ResponseFormatter()
    user = fmt.format_user_response(
        {
            "question": "create react native login and dashboard app",
            "intent": {"intent": "coding"},
            "technology": {
                "technology": "react native",
                "category": "mobile",
                "platform": "android_ios",
            },
            "plan": ["Create Login Screen", "Create Dashboard Screen"],
            "architecture": ["Login screen", "Dashboard screen", "Navigation"],
            "answer": "## Analysis\n- Intent: coding\n- Agents: master\n\n## Architecture\n- Nav stack\n",
            "evaluation": {"approved": True},
        }
    )
    low = user.lower()
    assert "react native" in low
    assert "agents:" not in low
    assert "create login screen" in low


def test_what_is_pm_in_india_user_mode():
    result = run_reasoning_pipeline("what is PM in India?")
    user = (result.get("answer") or result.get("user_response") or "").lower()
    assert "prime minister" in user
    assert "intent" not in user
    assert "agents" not in user
    assert "score" not in user
    assert "self critique" not in user
    assert "self-critique" not in user
    assert query_kind("what is PM in India?") == "knowledge"
    tech = result.get("technology") or {}
    assert not tech.get("technology")
    debug = result.get("debug") or {}
    assert debug.get("intent")


def test_react_native_login_screen_user_mode():
    result = run_reasoning_pipeline("create react native login screen", retrieve=False)
    user = (result.get("answer") or result.get("user_response") or "").lower()
    assert "react native" in user
    assert "implementation" in user
    assert "testing" in user
    assert "knowledge context" not in user
    assert "reflectionengine" not in user
    assert "confidence" not in user
    assert "agents:" not in user


def test_hello_has_no_pipeline_chrome():
    fmt = ResponseFormatter()
    user = fmt.format_user_response({"question": "hello"}).lower()
    assert "hello" in user
    assert "om" in user
    assert "agents" not in user
    assert "intent" not in user
    assert "postgresql" not in user
    brain = OMCognitiveBrain().process("hello")
    visible = (brain.get("user_response") or "").lower()
    assert "agents:" not in visible
    assert "self-critique" not in visible


def test_knowledge_filter_drops_unrelated_hits():
    flt = KnowledgeContextFilter()
    kept = flt.filter_hits(
        "create React Native dashboard",
        [
            "React Native navigation and mobile UI authentication.",
            "Newtonian physics and Maxwell electromagnetism.",
            "The Industrial Revolution and the steam engine.",
        ],
        technology={"technology": "react native"},
    )
    blob = " ".join(kept).lower()
    assert "react native" in blob
    assert "physics" not in blob
    assert "industrial revolution" not in blob
    civics = flt.filter_hits(
        "what is PM in India?",
        [
            "In India, PM means Prime Minister, the head of government.",
            "Build a FastAPI backend with PostgreSQL.",
            "React Native login screen example.",
        ],
    )
    civics_blob = " ".join(civics).lower()
    assert "prime minister" in civics_blob
    assert "fastapi" not in civics_blob
    assert "react native" not in civics_blob
