"""Cognitive brain smoke tests."""
from __future__ import annotations

from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain
from om_ai.core.response.response_formatter import ResponseFormatter
from om_ai.cognition.intent_engine import IntentEngine
from om_ai.cognition.task_planner import TaskPlanner


def test_brain_process_hello():
    result = OMCognitiveBrain().process("hello")
    assert isinstance(result, dict)
    text = str(result.get("user_response") or result.get("answer") or "")
    assert text.strip()
    assert "Agents:" not in text


def test_intent_and_planner_importable():
    intent = IntentEngine().analyze("create a login API")
    plan = TaskPlanner().decompose("create a login API")
    assert intent is not None
    assert isinstance(plan, dict)


def test_response_formatter_user_mode():
    fmt = ResponseFormatter()
    out = fmt.format_user_response({"question": "hello"})
    assert isinstance(out, str)
    assert out.strip()
