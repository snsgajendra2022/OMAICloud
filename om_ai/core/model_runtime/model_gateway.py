"""Authoritative Model Gateway for OM AI.

PHASE 6 - CANONICAL MODEL GATEWAY:
Make: om_ai.core.model_runtime.model_gateway.ModelGateway
the ONLY production model-generation interface.

Required API:
generate(
    prompt,
    *,
    context=None,
    max_new_tokens=None,
    temperature=None,
    top_p=None,
    stop=None,
    metadata=None
)

and:
chat(
    messages,
    *,
    context=None,
    generation_config=None,
    metadata=None
)

The gateway owns:
- model selection & resolution
- tokenizer
- checkpoint
- generation & decoding
- timeout & cancellation
- telemetry & observability
- quality validation
- error handling
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .generation_config import GenerationConfig
from .generation_result import GenerationResult
from .model_bundle import ModelBundle, ModelBundleManifest
from .model_loader import ProductionModelLoader
from .observability import GenerationTrace, get_tracer
from .production_tokenizer import TokenizerRegistry
from .quality_gate import GenerationQualityGate, get_quality_gate

logger = logging.getLogger(__name__)


class ModelGateway:
    """Single canonical authoritative entry point for OM model generation.

    Every higher-level component (ProductionBrain, API, Chat, Agents) uses this
    gateway instead of calling backends or engines directly.
    """

    _instance: ModelGateway | None = None

    def __init__(self, backend: Any | None = None) -> None:
        self._backend = backend
        self._quality_gate = get_quality_gate()
        self._tracer = get_tracer()

    @classmethod
    def get_instance(cls) -> ModelGateway:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _resolve_backend(self) -> Any:
        if self._backend is not None:
            return self._backend

        # Try active model loader backend first
        active = ProductionModelLoader.get_active_backend()
        if active is not None and getattr(active, "loaded", False):
            self._backend = active
            return active

        # Next check api_main native_backend
        try:
            from om_ai.api import main as api_main
            backend = getattr(api_main, "native_backend", None)
            if backend is not None and getattr(backend, "loaded", False):
                self._backend = backend
                return backend
        except Exception:
            pass

        # If still uninitialized, load using canonical ProductionModelLoader
        backend, _, _ = ProductionModelLoader.load_production_model(perform_smoke_test=False)
        self._backend = backend
        return backend

    def get_status(self) -> dict[str, Any]:
        """Return runtime readiness and bundle status."""
        try:
            backend = self._resolve_backend()
            ready = bool(backend and getattr(backend, "loaded", False) and getattr(backend, "_trained", False))
            return {
                "status": "READY" if ready else "STANDBY",
                "backend": type(backend).__name__,
                "ready": ready,
            }
        except Exception as exc:
            return {
                "status": "UNAVAILABLE",
                "backend": None,
                "ready": False,
                "error": str(exc),
            }

    def startup_health_check(self) -> dict[str, Any]:
        """Authoritative 7-point startup health check."""
        results: dict[str, Any] = {
            "checkpoint_exists": False,
            "checkpoint_loads": False,
            "tokenizer_loads": False,
            "vocab_matched": False,
            "model_initialized": False,
            "generation_succeeds": False,
            "quality_gate_passed": False,
            "status": "NOT READY",
            "error": None,
        }
        try:
            backend = self._resolve_backend()
            engine = getattr(backend, "engine", None)
            if not engine:
                raise RuntimeError("Engine not loaded on backend")

            # 1 & 2 Checkpoint
            if not engine.checkpoint_path or not getattr(engine, "model", None):
                raise RuntimeError("Checkpoint not loaded or missing")
            results["checkpoint_exists"] = True
            results["checkpoint_loads"] = True

            # 3 Tokenizer
            tok = getattr(engine, "tokenizer", None)
            if not tok:
                raise RuntimeError("Tokenizer not loaded")
            results["tokenizer_loads"] = True

            # 4 Vocab matched
            vocab_size = getattr(tok, "vocab_size", len(getattr(tok, "vocab", {})))
            manifest = ModelBundle.get_canonical_manifest()
            if vocab_size != manifest.vocab_size:
                raise RuntimeError(
                    f"Vocab mismatch: tokenizer={vocab_size}, manifest={manifest.vocab_size}"
                )
            results["vocab_matched"] = True
            results["model_initialized"] = True

            # 6 & 7 Test generation & quality gate
            gen_res = self.generate(
                "Hello",
                max_new_tokens=16,
                temperature=0.3,
            )
            if not gen_res.success:
                raise RuntimeError(f"Startup generation test failed: {gen_res.reason}")
            results["generation_succeeds"] = True
            results["quality_gate_passed"] = True
            results["status"] = "READY"
        except Exception as exc:
            results["error"] = str(exc)
            logger.warning("Startup health check incomplete: %s", exc)

        return results

    def generate(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stop: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        config: GenerationConfig | None = None,
    ) -> GenerationResult:
        start_t = time.perf_counter()
        prompt = str(prompt or "").strip()

        # Build config merging explicit params
        if config is not None:
            cfg = config
        else:
            cfg = GenerationConfig()
            if max_new_tokens is not None:
                cfg.max_new_tokens = max_new_tokens
            if temperature is not None:
                cfg.temperature = temperature
            if top_p is not None:
                cfg.top_p = top_p

        trace = GenerationTrace(
            route="ModelGateway.generate",
            temperature=cfg.temperature,
        )

        if not prompt:
            trace.error = "empty_prompt"
            self._tracer.record(trace)
            return GenerationResult(
                text="",
                success=False,
                reason="empty_prompt",
            )

        try:
            backend = self._resolve_backend()
            raw_text = self._call_backend_generate(backend, prompt, cfg, context or {})
            text = self._clean(raw_text)

            # Evaluate with 6-stage Quality Gate
            q_res = self._quality_gate.evaluate(text, prompt=prompt)
            duration_ms = (time.perf_counter() - start_t) * 1000

            trace.generation_time_ms = duration_ms
            trace.tokens = len(text.split())
            trace.quality_score = q_res.quality_score

            if not q_res.passed:
                trace.error = q_res.reason
                self._tracer.record(trace)
                return GenerationResult(
                    text="",
                    success=False,
                    rejected=True,
                    quality=q_res.quality_score,
                    reason=q_res.reason,
                )

            self._tracer.record(trace)
            return GenerationResult(
                text=text,
                success=True,
                quality=q_res.quality_score,
                metadata={
                    "backend": type(backend).__name__,
                    "temperature": cfg.temperature,
                    "generation_time_ms": duration_ms,
                    **(metadata or {}),
                },
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_t) * 1000
            trace.generation_time_ms = duration_ms
            trace.error = f"{type(exc).__name__}: {exc}"
            self._tracer.record(trace)
            logger.exception("OM generation failed")

            return GenerationResult(
                text="",
                success=False,
                rejected=True,
                reason=f"{type(exc).__name__}: {exc}",
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        context: dict[str, Any] | None = None,
        generation_config: GenerationConfig | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GenerationResult:
        start_t = time.perf_counter()
        cfg = generation_config or GenerationConfig()

        trace = GenerationTrace(
            route="ModelGateway.chat",
            temperature=cfg.temperature,
        )

        if not messages:
            trace.error = "empty_messages"
            self._tracer.record(trace)
            return GenerationResult(text="", success=False, reason="empty_messages")

        try:
            backend = self._resolve_backend()
            kwargs = cfg.to_kwargs()

            if hasattr(backend, "chat"):
                res = backend.chat(messages, **kwargs)
                raw_text = self._extract_text(res)
            elif hasattr(backend, "generate"):
                # Fallback to plain prompt reconstruction
                user_msg = messages[-1].get("content", "")
                raw_text = self._call_backend_generate(backend, user_msg, cfg, context or {})
            else:
                raise RuntimeError(f"Backend {type(backend).__name__} does not support chat/generate")

            text = self._clean(raw_text)
            last_prompt = messages[-1].get("content", "") if messages else ""
            q_res = self._quality_gate.evaluate(text, prompt=last_prompt)
            duration_ms = (time.perf_counter() - start_t) * 1000

            trace.generation_time_ms = duration_ms
            trace.tokens = len(text.split())
            trace.quality_score = q_res.quality_score

            if not q_res.passed:
                trace.error = q_res.reason
                self._tracer.record(trace)
                return GenerationResult(
                    text="",
                    success=False,
                    rejected=True,
                    quality=q_res.quality_score,
                    reason=q_res.reason,
                )

            self._tracer.record(trace)
            return GenerationResult(
                text=text,
                success=True,
                quality=q_res.quality_score,
                metadata={
                    "backend": type(backend).__name__,
                    "temperature": cfg.temperature,
                    "generation_time_ms": duration_ms,
                    **(metadata or {}),
                },
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_t) * 1000
            trace.generation_time_ms = duration_ms
            trace.error = f"{type(exc).__name__}: {exc}"
            self._tracer.record(trace)
            logger.exception("OM chat generation failed")

            return GenerationResult(
                text="",
                success=False,
                rejected=True,
                reason=f"{type(exc).__name__}: {exc}",
            )

    def _call_backend_generate(
        self,
        backend: Any,
        prompt: str,
        cfg: GenerationConfig,
        context: dict[str, Any],
    ) -> str:
        kwargs = cfg.to_kwargs()

        if hasattr(backend, "generate"):
            try:
                res = backend.generate(prompt, **kwargs)
                return self._extract_text(res)
            except TypeError:
                res = backend.generate(prompt)
                return self._extract_text(res)

        if hasattr(backend, "chat"):
            messages = [{"role": "user", "content": prompt}]
            try:
                res = backend.chat(messages, **kwargs)
                return self._extract_text(res)
            except TypeError:
                res = backend.chat(messages)
                return self._extract_text(res)

        raise RuntimeError(
            f"Backend {type(backend).__name__} has no chat/generate method"
        )

    @staticmethod
    def _extract_text(result: Any) -> str:
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, tuple) and len(result) > 0:
            return str(result[0])
        if isinstance(result, dict):
            for key in ("answer", "text", "content", "response", "generated_text"):
                val = result.get(key)
                if isinstance(val, str):
                    return val
        return str(result)

    @staticmethod
    def _clean(text: str) -> str:
        return str(text or "").replace("\x00", "").strip()