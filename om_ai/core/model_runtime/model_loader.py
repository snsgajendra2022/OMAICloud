"""Authoritative Production Model Initializer for OM AI.

PHASE 5 - MODEL INITIALIZATION:
Conceptually: ProductionModelLoader

Responsibilities:
- load config
- load tokenizer
- instantiate architecture
- load checkpoint
- move to device
- configure dtype
- set eval mode
- validate model
- perform generation smoke test

Startup sequence:
CONFIG -> TOKENIZER -> MODEL -> CHECKPOINT -> COMPATIBILITY -> DEVICE -> GENERATION TEST -> READY
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import torch

from om_ai.backends.om_native import OMNativeBackend
from om_ai.core.model_runtime.checkpoint_loader import ProductionCheckpointLoader
from om_ai.core.model_runtime.model_bundle import ProductionModelBundle, get_production_bundle
from om_ai.core.model_runtime.production_tokenizer import (
    ProductionTokenizer,
    TokenizerRegistry,
    validate_model_tokenizer,
)
from om_ai.core.model_runtime.quality_gate import get_quality_gate
from om_ai.runtime.engine import LocalLLMEngine

logger = logging.getLogger(__name__)


class ModelInitializationError(RuntimeError):
    """Raised when production model initialization or smoke test fails."""
    pass


class ProductionModelLoader:
    """Canonical production model loader executing the strict 8-step startup sequence."""

    _active_backend: OMNativeBackend | None = None
    _active_bundle: ProductionModelBundle | None = None
    _active_tokenizer: ProductionTokenizer | None = None

    @classmethod
    def load_production_model(
        cls,
        bundle: ProductionModelBundle | None = None,
        *,
        device: str | None = None,
        perform_smoke_test: bool = True,
        root: Path | None = None,
    ) -> tuple[OMNativeBackend, ProductionTokenizer, ProductionModelBundle]:
        """Execute strict initialization sequence."""
        base = root or Path(".")
        
        # 1. Config & Bundle
        if bundle is None:
            bundle = get_production_bundle(base)
        bundle.validate(base)
        logger.info("Step 1: Configuration & Bundle valid for %s", bundle.model_id)

        # 2. Tokenizer
        tokenizer = TokenizerRegistry.get_canonical(base / bundle.tokenizer_path)
        logger.info("Step 2: Canonical tokenizer loaded with vocab %d", tokenizer.vocab_size)

        # 3 & 4. Architecture & Checkpoint
        engine = LocalLLMEngine()
        backend = OMNativeBackend(engine=engine)
        target_device = device or ("mps" if torch.backends.mps.is_available() else "cpu")

        info = backend.load(
            config_path=str(base / bundle.config_path),
            tokenizer_path=str(base / bundle.tokenizer_path),
            checkpoint_path=str(base / bundle.checkpoint_path),
            device=target_device,
            require_checkpoint=True,
        )
        logger.info("Steps 3 & 4: Model architecture & Checkpoint loaded on %s", target_device)

        # 5. Compatibility validation
        model_obj = getattr(engine, "model", None)
        if model_obj is None:
            raise ModelInitializationError("Model object was not instantiated")
        validate_model_tokenizer(model_obj, tokenizer)
        logger.info("Step 5: Model and tokenizer compatibility verified")

        # 6. Device & Eval mode
        model_obj.eval()
        logger.info("Step 6: Model set to eval mode on device %s", target_device)

        # 7. Smoke Generation Test
        if perform_smoke_test:
            try:
                smoke_out = backend.generate("Hello", max_new_tokens=15, temperature=0.2)
                smoke_text = str(smoke_out or "").strip()
                if not smoke_text:
                    raise ModelInitializationError("Smoke generation returned empty output")
                qgate = get_quality_gate()
                q_res = qgate.evaluate(smoke_text, prompt="Hello", min_chars=1)
                if not q_res.passed:
                    raise ModelInitializationError(f"Smoke generation failed quality gate: {q_res.reason}")
                logger.info("Step 7: Smoke generation test PASSED (sample: %r)", smoke_text[:30])
            except Exception as exc:
                raise ModelInitializationError(f"Generation smoke test failed: {exc}") from exc

        # 8. Ready
        bundle.status = "READY"
        cls._active_backend = backend
        cls._active_bundle = bundle
        cls._active_tokenizer = tokenizer

        return backend, tokenizer, bundle

    @classmethod
    def get_active_backend(cls) -> OMNativeBackend | None:
        return cls._active_backend

    @classmethod
    def get_active_tokenizer(cls) -> ProductionTokenizer | None:
        return cls._active_tokenizer

    @classmethod
    def get_active_bundle(cls) -> ProductionModelBundle | None:
        return cls._active_bundle
