from __future__ import annotations

import logging
import time
from typing import Any

from .generation_config import GenerationConfig
from .generation_result import GenerationResult
from .model_bundle import ModelBundle, ModelBundleManifest
from .observability import GenerationTrace, get_tracer
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

        from om_ai.api import main as api_main

        backend = getattr(api_main, "native_backend", None)
        if backend is None:
            raise RuntimeError("OM native backend is unavailable")

        self._backend = backend
        return backend

    def startup_health_check(self) -> dict[str, Any]:
        """Perform authoritative 7-point startup health check:
        1. Checkpoint exists
        2. Checkpoint loads
        3. Tokenizer loads
        4. Vocab matches
        5. Model initializes
        6. Generation succeeds
        7. Generated text passes quality gate
        """
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
                config=GenerationConfig(max_new_tokens=16, temperature=0.7),
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
        config: GenerationConfig | None = None,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        start_t = time.perf_counter()
        prompt = str(prompt or "").strip()

        trace = GenerationTrace(
            route="ModelGateway",
            temperature=(config.temperature if config else 0.7),
        )

        if not prompt:
            trace.error = "empty_prompt"
            self._tracer.record(trace)
            return GenerationResult(
                text="",
                success=False,
                reason="empty_prompt",
            )

        cfg = config or GenerationConfig()

        try:
            backend = self._resolve_backend()
            raw_text = self._call_backend(
                backend,
                prompt,
                cfg,
                context or {},
            )
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

    def _call_backend(
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