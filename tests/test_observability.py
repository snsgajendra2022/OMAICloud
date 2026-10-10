from __future__ import annotations

import json

import pytest

from om_ai.runtime.observability import current_trace, trace_request, trace_span


def test_trace_request_binds_and_resets_context(tmp_path, monkeypatch):
    sink = tmp_path / "trace.jsonl"
    monkeypatch.setenv("OM_TRACE_JSONL", str(sink))
    before = current_trace()
    with trace_request(request_id="req-test", conversation_id="conv-test", model_id="om-test") as ids:
        assert ids["request_id"] == "req-test"
        assert current_trace()["trace_id"] == ids["trace_id"]
        with trace_span("model.generate", attributes={"output_tokens": 4, "prompt": "must not log"}):
            pass
    assert current_trace() == before
    events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    assert [event["event"] for event in events] == [
        "request.start", "span.start", "span.end", "request.end"
    ]
    assert all("prompt" not in event for event in events)
    assert all(event["request_id"] == "req-test" for event in events)


def test_trace_records_errors_and_reraises(tmp_path, monkeypatch):
    sink = tmp_path / "trace.jsonl"
    monkeypatch.setenv("OM_TRACE_JSONL", str(sink))
    with pytest.raises(ValueError):
        with trace_request(request_id="req-error"):
            with trace_span("generation"):
                raise ValueError("example")
    events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    assert any(event["event"] == "span.error" and event["error_type"] == "ValueError" for event in events)
    assert any(event["event"] == "request.error" for event in events)
