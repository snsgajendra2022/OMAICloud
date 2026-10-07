"""Authoritative Model Bundle Manifest definition and validator."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ModelBundleManifest:
    model_name: str = "OM-1.0"
    model_version: str = "1.0.0"
    model_architecture: str = "LlamaForCausalLM"
    checkpoint_path: str = "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt"
    tokenizer_path: str = "artifacts/tokenizer-production-65536.json"
    vocab_size: int = 65536
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
    context_length: int = 2048
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
            "model_architecture": self.model_architecture,
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
        return cls(**data)


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
