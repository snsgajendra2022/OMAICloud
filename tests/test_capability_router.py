from __future__ import annotations

from om_ai.core.intelligence import capability_router as router


def test_native_synthesize_uses_om_native_chat(monkeypatch):
    calls = {}

    class FakeNative:
        def chat(self, messages, **kwargs):
            calls["messages"] = messages
            calls["kwargs"] = kwargs
            return "Use a bounded retry policy and exponential backoff for transient failures."

    monkeypatch.setattr("om_ai.backends.om_native.OMNativeBackend", FakeNative)
    result = router._native_synthesize(
        "How should retries work?",
        "research",
        {"project_hint": "Python API client"},
        {"intent": "question"},
        tool_text="The service returns HTTP 503 for temporary overload.",
    )
    assert result.startswith("Use a bounded retry policy")
    assert any(m["role"] == "system" and "OM's own native model weights" in m["content"] for m in calls["messages"])
    assert "HTTP 503" in calls["messages"][-1]["content"]
    assert calls["kwargs"]["max_new_tokens"] >= 64


def test_native_synthesize_rejects_static_stub(monkeypatch):
    class FakeNative:
        def chat(self, messages, **kwargs):
            return "Here's a clear take: define the outcome and break it into actionable steps."

    monkeypatch.setattr("om_ai.backends.om_native.OMNativeBackend", FakeNative)
    assert router._native_synthesize(
        "Help me implement retries", "coding", {}, {}
    ) == ""


def test_native_only_capability_failure_does_not_return_canned_handler(monkeypatch):
    monkeypatch.setattr(router, "_native_synthesize", lambda *args, **kwargs: "")
    monkeypatch.setattr(router, "_cap_research", lambda *args, **kwargs: "Here is a clear useful answer grounded in the request.")
    result = router.CapabilityRouter().execute(
        {"capability": "research", "handler": router._cap_research},
        "Explain a topic",
        {},
        {},
    )
    assert "native model could not produce" in result.lower()
