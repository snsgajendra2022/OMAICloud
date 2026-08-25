"""Model Gateway — never expose models directly to clients."""
from __future__ import annotations

import time
from typing import Any

from services._common import ServiceHealth, ok


class ModelGateway:
    """Route / fallback / token accounting for OM model families."""

    CATALOG = {
        "om-1.0": {"role": "foundation", "status": "local"},
        "om-1b": {"role": "small", "status": "config_ready"},
        "om-7b": {"role": "mid", "status": "config_ready"},
        "om-70b": {"role": "large", "status": "config_ready"},
        "embedding": {"role": "retrieval", "status": "tfidf_local"},
        "vision": {"role": "multimodal", "status": "stub"},
        "speech": {"role": "multimodal", "status": "stub"},
    }

    def __init__(self) -> None:
        self._tokens_in = 0
        self._tokens_out = 0
        self._requests = 0
        self._errors = 0

    def health(self) -> dict[str, Any]:
        return ServiceHealth(
            "model-gateway",
            detail={"catalog": list(self.CATALOG), "requests": self._requests},
        ).to_dict()

    def select_model(self, task: str = "", preferred: str = "") -> str:
        t = (task or "").lower()
        if preferred and preferred in self.CATALOG:
            return preferred
        if any(w in t for w in ("image", "screenshot", "vision")):
            return "vision"
        if any(w in t for w in ("voice", "speech", "audio")):
            return "speech"
        if "embed" in t or "retrieve" in t:
            return "embedding"
        # Prefer local ready model
        return "om-1.0"

    def route(self, prompt: str, *, preferred: str = "", max_tokens: int = 256) -> dict[str, Any]:
        self._requests += 1
        model = self.select_model(prompt, preferred)
        started = time.time()
        text = ""
        backend = "heuristic"
        try:
            if model == "om-1.0":
                from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
                from om_ai.core.response.intelligence import ensure_intelligent_response

                md = run_reasoning_pipeline(prompt, retrieve=True).get("markdown") or ""
                repaired = ensure_intelligent_response(prompt, md, intent="chat")
                text = repaired.get("final") or md
                backend = "om-reasoning+quality"
            elif model == "embedding":
                from om_ai.knowledge.retrieval import VectorKnowledgeLayer

                hits = VectorKnowledgeLayer().search(prompt, k=3)
                text = "\n".join(str(h.get("text", ""))[:200] for h in hits) or "(no hits)"
                backend = "vector-knowledge"
            else:
                text = (
                    f"Model '{model}' is registered ({self.CATALOG[model]['status']}). "
                    "Weights/configs ready path — use training platform to produce checkpoints."
                )
                backend = "catalog-stub"
            approx_in = max(1, len(prompt.split()))
            approx_out = max(1, len(text.split()))
            self._tokens_in += approx_in
            self._tokens_out += approx_out
            return ok(
                {
                    "model": model,
                    "text": text,
                    "backend": backend,
                    "latency_ms": int((time.time() - started) * 1000),
                    "usage": {"tokens_in": approx_in, "tokens_out": approx_out},
                    "fallback": None,
                }
            )
        except Exception as exc:
            self._errors += 1
            # fallback to structured reasoning
            try:
                from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

                text = run_reasoning_pipeline(prompt, retrieve=False).get("markdown") or str(exc)
                return ok(
                    {
                        "model": "om-1.0",
                        "text": text,
                        "backend": "fallback-reasoning",
                        "fallback": str(exc),
                        "latency_ms": int((time.time() - started) * 1000),
                    }
                )
            except Exception as exc2:
                return {"ok": False, "error": str(exc2), "primary_error": str(exc)}

    def metrics(self) -> dict[str, Any]:
        return {
            "requests": self._requests,
            "errors": self._errors,
            "tokens_in": self._tokens_in,
            "tokens_out": self._tokens_out,
            "catalog": self.CATALOG,
        }
