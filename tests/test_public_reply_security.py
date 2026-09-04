"""Tests for public reply sanitizer + context intent tool decision."""
from __future__ import annotations

from om_ai.core.understanding.context_intent import classify_context_intent
from om_ai.runtime.public_reply import sanitize_public_reply, is_safe_public_answer
from om_ai.runtime.chat_pipeline import run_chat_pipeline


LEAK = """
## Knowledge Brain
OM AI Foundation sample.
## Memory
[layered] User: hi
## Connected systems
[decision] {'goal': 'x'}
Today's date is Friday, 04 September 2026.
"""


def test_sanitize_strips_internals():
    out = sanitize_public_reply(LEAK)
    assert "Knowledge Brain" not in out
    assert "[layered]" not in out
    assert "[decision]" not in out
    assert "Connected systems" not in out


def test_context_intent_date_vs_conversation():
    assert classify_context_intent("good moring om how was your date")["intent"] == "conversation"
    assert classify_context_intent("What is today's date?")["intent"] == "date_query"
    assert classify_context_intent("What is today's date?")["use_tools"] is True


def test_pipeline_no_leak_on_greeting():
    out = run_chat_pipeline("good morning om how was your day")
    ans = out["answer"]
    assert is_safe_public_answer(ans)
    assert "Knowledge Brain" not in ans
    assert "[tool:date]" not in ans
    assert "Foundation sample" not in ans


def test_pipeline_clean_date():
    out = run_chat_pipeline("What is today's date?")
    ans = out["answer"]
    assert "Today's date is" in ans
    assert "Knowledge Brain" not in ans
    assert "[tool:" not in ans
