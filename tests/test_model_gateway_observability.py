from __future__ import annotations

import json

from om_ai.runtime.model_gateway import ModelGateway


class Backend:
    def health(self):
        return {"ok": True}

    def generate(self, prompt, **kwargs):
        return "A verified test answer."

    def chat(self, messages, **kwargs):
        return "A verified test answer."

    def generate_stream(self, prompt, **kwargs):
        yield "A "
        yield "streamed answer."

    def stream_chat(self, messages, **kwargs):
        yield "A streamed answer."


def test_gateway_operations_emit_spans_without_logging_prompts(tmp_path, monkeypatch):
    sink = tmp_path / "gateway-trace.jsonl"
    monkeypatch.setenv("OM_TRACE_JSONL", str(sink))
    gateway = ModelGateway(Backend())
    assert gateway.generate("secret prompt must not appear") == "A verified test answer."
    assert "".join(gateway.stream_generate("another secret prompt")) == "A streamed answer."
    events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    spans = [event.get("span") for event in events if event["event"] == "span.end"]
    assert spans == ["model_gateway.generate", "model_gateway.stream_generate"]
    assert "secret prompt" not in sink.read_text(encoding="utf-8")
