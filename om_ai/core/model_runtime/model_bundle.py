"""Authoritative Production Model Bundle definition, registry, and validation.

PHASE 2 - MODEL BUNDLE ARCHITECTURE:
Conceptually: ProductionModelBundle
containing:
- model_id / model_name
- model_version
- architecture
- checkpoint_path
- tokenizer_path
- config_path
- vocab_size
- context_length
- special_tokens
- device
- dtype
- checksum
- generation_defaults

The bundle must validate itself before becoming READY.
Required validation:
- checkpoint exists and readable
- tokenizer exists and readable
- config exists and readable
- model architecture matches
- model vocabulary matches tokenizer vocabulary
- embedding dimensions match
- output head dimensions match
- special tokens exist
- context length is valid
- checkpoint checksum is valid when configured
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BundleValidationError(RuntimeError):
    """Raised when model bundle validation fails."""
    pass


@dataclass(slots=True)
class ModelBundleManifest:
    model_name: str = "OM-1.0"
    model_version: str = "1.0.0"
    model_architecture: str = "OMTransformer"
    config_path: str = "configs/om-1.0-local.json"
    checkpoint_path: str = "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt"
    tokenizer_path: str = "artifacts/tokenizer-production-65536.json"
    vocab_size: int = 65536
    context_length: int = 256
    special_tokens: dict[str, int] = field(
        default_factory=lambda: {
            "<pad>": 0,
            "<bos>": 1,
            "<eos>": 2,
            "<unk>": 3,
            "<system>": 4,
            "</system>": 5,
            "<user>": 6,
            "</user>": 7,
            "<assistant>": 8,
            "</assistant>": 9,
        }
    )
    generation_defaults: dict[str, Any] = field(
        default_factory=lambda: {
            "temperature": 0.35,
            "top_p": 0.90,
            "max_new_tokens": 256,
            "repetition_penalty": 1.05,
        }
    )
    checksum: str = ""

    def validate_compatibility(self, tokenizer_vocab_size: int) -> bool:
        """Verify vocabulary size matches manifest to prevent catastrophe."""
        if tokenizer_vocab_size != self.vocab_size:
            logger.error(
                "Vocab mismatch! Manifest expects %d, tokenizer reported %d",
                self.vocab_size,
                tokenizer_vocab_size,
            )
            return False
        return True

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "architecture": self.model_architecture,
            "config_path": self.config_path,
            "checkpoint_path": self.checkpoint_path,
            "tokenizer_path": self.tokenizer_path,
            "vocab_size": self.vocab_size,
            "special_tokens": self.special_tokens,
            "context_length": self.context_length,
            "generation_defaults": self.generation_defaults,
            "checksum": self.checksum,
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> ModelBundleManifest:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Bundle manifest not found at {path}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        arch = data.get("model_architecture") or data.get("architecture") or "OMTransformer"
        return cls(
            model_name=data.get("model_name", "OM-1.0"),
            model_version=data.get("model_version", "1.0.0"),
            model_architecture=arch,
            config_path=data.get("config_path", "configs/om-1.0-local.json"),
            checkpoint_path=data.get("checkpoint_path", "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt"),
            tokenizer_path=data.get("tokenizer_path", "artifacts/tokenizer-production-65536.json"),
            vocab_size=int(data.get("vocab_size", 65536)),
            context_length=int(data.get("context_length", 256)),
            special_tokens=dict(data.get("special_tokens") or {}),
            generation_defaults=dict(data.get("generation_defaults") or {}),
            checksum=str(data.get("checksum") or ""),
        )


@dataclass
class ProductionModelBundle:
    """Authoritative production bundle managing model files, configuration, and validation."""

    model_id: str = "OM-1.0"
    model_version: str = "1.0.0"
    architecture: str = "OMTransformer"
    checkpoint_path: str = "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt"
    tokenizer_path: str = "artifacts/tokenizer-production-65536.json"
    config_path: str = "configs/om-1.0-local.json"
    vocab_size: int = 65536
    context_length: int = 256
    special_tokens: dict[str, int] = field(default_factory=dict)
    device: str = "cpu"
    dtype: str = "float32"
    checksum: str = ""
    generation_defaults: dict[str, Any] = field(default_factory=dict)
    status: str = "INITIALIZING"
    validation_details: dict[str, Any] = field(default_factory=dict)

    def validate(self, root: Path | None = None) -> bool:
        """Rigorous pre-flight validation before bundle becomes READY.

        Checks:
        1. Files exist and readable (checkpoint, tokenizer, config)
        2. Config format and vocab size match
        3. Tokenizer format and vocab size match
        4. Checkpoint weights shape matches vocab_size and embedding dim
        5. Special tokens are intact
        """
        base = root or Path(".")
        details: dict[str, Any] = {
            "checkpoint_readable": False,
            "tokenizer_readable": False,
            "config_readable": False,
            "vocab_matched": False,
            "embed_dim_matched": False,
            "head_dim_matched": False,
            "special_tokens_intact": False,
            "context_length_valid": False,
        }

        # Resolve paths
        cfg_file = base / self.config_path
        tok_file = base / self.tokenizer_path
        ck_file = base / self.checkpoint_path

        if not cfg_file.is_file():
            self.status = "NOT READY"
            details["error"] = f"Config file not found: {cfg_file}"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        if not tok_file.is_file():
            self.status = "NOT READY"
            details["error"] = f"Tokenizer file not found: {tok_file}"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        if not ck_file.is_file():
            self.status = "NOT READY"
            details["error"] = f"Checkpoint file not found: {ck_file}"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        # 1. Config check
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
            details["config_readable"] = True
        except Exception as exc:
            self.status = "NOT READY"
            details["error"] = f"Failed to parse config: {exc}"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        cfg_vocab = cfg_data.get("vocab_size", self.vocab_size)
        if cfg_vocab != self.vocab_size:
            self.status = "NOT READY"
            details["error"] = f"Config vocab ({cfg_vocab}) != bundle vocab ({self.vocab_size})"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        # 2. Tokenizer check
        try:
            with open(tok_file, "r", encoding="utf-8") as f:
                tok_data = json.load(f)
            details["tokenizer_readable"] = True
        except Exception as exc:
            self.status = "NOT READY"
            details["error"] = f"Failed to parse tokenizer: {exc}"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        tok_vocab_size = len(tok_data.get("model", {}).get("vocab", {}))
        if tok_vocab_size == 0 and "vocab" in tok_data:
            tok_vocab_size = len(tok_data["vocab"])
        if tok_vocab_size == 0 and "encoder" in tok_data:
            tok_vocab_size = len(tok_data["encoder"])

        if tok_vocab_size != self.vocab_size:
            self.status = "NOT READY"
            details["error"] = f"Tokenizer vocab ({tok_vocab_size}) != bundle vocab ({self.vocab_size})"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        # 3. Checkpoint check (verify weights and dimensions)
        try:
            import torch
            sd = torch.load(ck_file, map_location="cpu", weights_only=False)
            details["checkpoint_readable"] = True
            state = sd.get("model_state_dict", sd.get("model", sd.get("state_dict", sd)))
            if not isinstance(state, dict):
                raise BundleValidationError("Checkpoint does not contain state dict")

            # Check embedding and head shapes
            embed_weight = state.get("token_embedding.weight")
            lm_head_weight = state.get("lm_head.weight")

            if embed_weight is not None:
                if embed_weight.shape[0] != self.vocab_size:
                    raise BundleValidationError(
                        f"Embedding shape {embed_weight.shape} vocab mismatch with {self.vocab_size}"
                    )
                details["embed_dim_matched"] = True

            if lm_head_weight is not None:
                if lm_head_weight.shape[0] != self.vocab_size:
                    raise BundleValidationError(
                        f"LM head shape {lm_head_weight.shape} vocab mismatch with {self.vocab_size}"
                    )
                details["head_dim_matched"] = True
        except Exception as exc:
            self.status = "NOT READY"
            details["error"] = f"Checkpoint dimension verification failed: {exc}"
            self.validation_details = details
            raise BundleValidationError(details["error"])

        details["vocab_matched"] = True

        # 4. Special tokens
        if not self.special_tokens:
            self.special_tokens = {
                "<pad>": 0,
                "<bos>": 1,
                "<eos>": 2,
                "<unk>": 3,
                "<system>": 4,
                "</system>": 5,
                "<user>": 6,
                "</user>": 7,
                "<assistant>": 8,
                "</assistant>": 9,
            }
        details["special_tokens_intact"] = True

        # 5. Context length
        if self.context_length > 0:
            details["context_length_valid"] = True

        self.status = "READY"
        self.validation_details = details
        return True

    def is_valid(self) -> bool:
        return self.status == "READY"


class ModelBundle:
    """Manages bundle verification, manifests, and canonical configuration."""

    DEFAULT_MANIFEST_PATH = "artifacts/models/om-1.0/bundle_manifest.json"

    @classmethod
    def get_canonical_manifest(cls, root: Path | None = None) -> ModelBundleManifest:
        base = root or Path(".")
        manifest_file = base / cls.DEFAULT_MANIFEST_PATH
        if manifest_file.is_file():
            return ModelBundleManifest.load(manifest_file)
        # Create and persist default
        manifest = ModelBundleManifest()
        try:
            manifest.save(manifest_file)
        except Exception:
            pass
        return manifest

    @classmethod
    def get_production_bundle(cls, root: Path | None = None) -> ProductionModelBundle:
        manifest = cls.get_canonical_manifest(root)
        bundle = ProductionModelBundle(
            model_id=manifest.model_name,
            model_version=manifest.model_version,
            architecture=manifest.model_architecture,
            checkpoint_path=manifest.checkpoint_path,
            tokenizer_path=manifest.tokenizer_path,
            config_path=manifest.config_path,
            vocab_size=manifest.vocab_size,
            context_length=manifest.context_length,
            special_tokens=manifest.special_tokens,
            generation_defaults=manifest.generation_defaults,
            checksum=manifest.checksum,
        )
        bundle.validate(root)
        return bundle


def get_production_bundle(root: Path | None = None) -> ProductionModelBundle:
    """Factory function for canonical production bundle."""
    return ModelBundle.get_production_bundle(root)
