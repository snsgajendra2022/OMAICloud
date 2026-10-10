from __future__ import annotations

import pytest

from om_ai.runtime.model_gateway import ModelGateway, ModelGatewayError


class FakeBackend:
    def __init__(self, *, ready: bool = True, text: str = "Python is a programming language."):
        self.ready = ready
        self.text = text

    def health(self):
        return {"ok": self.ready}

    def generate(self, prompt, **kwargs):
        return self.text

    def chat(self, messages, **kwargs):
        return self.text

    def generate_stream(self, prompt, **kwargs):
        yield "Python "
        yield "is useful."


def test_gateway_generates_from_ready_backend():
    gateway = ModelGateway(FakeBackend())
    assert gateway.generate("What is Python?") == "Python is a programming language."


def test_gateway_fails_closed_when_backend_not_ready():
    gateway = ModelGateway(FakeBackend(ready=False))
    with pytest.raises(ModelGatewayError, match="not ready"):
        gateway.generate("What is Python?")


def test_gateway_rejects_empty_or_degenerate_generation():
    gateway = ModelGateway(FakeBackend(text=""))
    with pytest.raises(ModelGatewayError, match="no usable text"):
        gateway.generate("Say hello")

    garbage = "C_yAI*uing att(;e potoentPEZec random token soup"
    gateway = ModelGateway(FakeBackend(text=garbage))
    with pytest.raises(ModelGatewayError, match="output-integrity"):
        gateway.generate("Explain Python")


def test_gateway_streams_native_chunks():
    gateway = ModelGateway(FakeBackend())
    assert "".join(gateway.stream_generate("Explain Python")) == "Python is useful."


def test_gateway_does_not_fake_embeddings():
    gateway = ModelGateway(FakeBackend())
    with pytest.raises(NotImplementedError, match="no certified native embedding model"):
        gateway.embed(["hello"])
