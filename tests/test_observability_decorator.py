"""Tests for OM's request observability contract."""
from __future__ import annotations

import json

from om_ai.runtime.observability import current_trace, trace_function


def test_trace_function_creates_request_and_stage_spans(tmp_path, monkeypatch):
    sink = tmp_path / "trace.jsonl"
    monkeypatch.setenv("OM_TRACE_JSONL", str(sink))

    @trace_function("test.entrypoint")
    def entrypoint(*, conversation_id: str, text: str) -> str:
        assert current_trace()["conversation_id"] == conversation_id
        return "ok"

    assert entrypoint(conversation_id="conv-123", text="private prompt") == "ok"
    events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    assert [event["event"] for event in events] == [
        "request.start", "span.start", "span.end", "request.end"
    ]
    assert all(event.get("span") != "private prompt" for event in events)
    assert all("private prompt" not in json.dumps(event) for event in events)
    assert current_trace()["trace_id"] is None
