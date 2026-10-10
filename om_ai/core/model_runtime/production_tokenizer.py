"""Canonical Production Tokenizer & Registry for OM AI.

PHASE 3 - TOKENIZER SYSTEM:
Implement:
- TokenizerRegistry
- ProductionTokenizer
- validate_model_tokenizer(model, tokenizer)

Responsibilities:
- load
- encode
- decode
- special token handling (<pad>, <bos>, <eos>, <unk>, <system>, </system>, <user>, </user>, <assistant>, </assistant>)
- vocabulary validation
- padding
- truncation
- attention mask
- BOS/EOS handling
- unknown token handling
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from om_ai.tokenizer.loader import (
    load_tokenizer,
    tokenizer_fingerprint,
    tokenizer_sha256,
)

logger = logging.getLogger(__name__)


class TokenizerValidationError(RuntimeError):
    """Raised when tokenizer validation or compatibility fails."""
    pass


class ProductionTokenizer:
    """Authoritative production wrapper around canonical OM tokenizer."""

    def __init__(self, raw_tokenizer: Any, *, path: str | Path | None = None) -> None:
        self._tok = raw_tokenizer
        self._path = str(path) if path else getattr(raw_tokenizer, "_source_path", "")
        self._validate_special_tokens()

    def _validate_special_tokens(self) -> None:
        required = [
            "<pad>", "<bos>", "<eos>", "<unk>",
            "<system>", "</system>",
            "<user>", "</user>",
            "<assistant>", "</assistant>",
        ]
        for tok in required:
            try:
                tid = self._tok._id(tok) if hasattr(self._tok, "_id") else self._tok.vocab.get(tok)
                if tid is None:
                    raise TokenizerValidationError(f"Tokenizer missing required special token: {tok}")
            except Exception as exc:
                raise TokenizerValidationError(f"Failed to check token '{tok}': {exc}") from exc

    @property
    def vocab_size(self) -> int:
        return int(getattr(self._tok, "vocab_size", len(getattr(self._tok, "vocab", {}))))

    @property
    def pad_id(self) -> int:
        return int(self._tok.pad_id)

    @property
    def bos_id(self) -> int:
        return int(self._tok.bos_id)

    @property
    def eos_id(self) -> int:
        return int(self._tok.eos_id)

    @property
    def unk_id(self) -> int:
        return int(self._tok.unk_id)

    @property
    def system_id(self) -> int:
        return int(self._tok.system_id)

    @property
    def system_end_id(self) -> int:
        return int(self._tok.system_end_id)

    @property
    def user_id(self) -> int:
        return int(self._tok.user_id)

    @property
    def user_end_id(self) -> int:
        return int(self._tok.user_end_id)

    @property
    def assistant_id(self) -> int:
        return int(self._tok.assistant_id)

    @property
    def assistant_end_id(self) -> int:
        return int(self._tok.assistant_end_id)

    @property
    def fingerprint(self) -> str:
        return str(getattr(self._tok, "fingerprint", "") or "")

    def encode(
        self,
        text: str,
        *,
        add_bos: bool = False,
        add_eos: bool = False,
        max_length: int | None = None,
        truncation: bool = False,
    ) -> list[int]:
        ids = list(self._tok.encode(text, add_bos=add_bos, add_eos=add_eos))
        if truncation and max_length is not None and len(ids) > max_length:
            if add_eos and ids[-1] == self.eos_id:
                ids = ids[:max_length - 1] + [self.eos_id]
            else:
                ids = ids[:max_length]
        return ids

    def decode(self, ids: list[int], *, skip_special_tokens: bool = True) -> str:
        if hasattr(self._tok, "decode"):
            return self._tok.decode([int(x) for x in ids])
        return ""

    def encode_chat(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool = True,
        max_length: int | None = None,
    ) -> list[int]:
        ids = list(self._tok.encode_chat(
            messages,
            add_generation_prompt=add_generation_prompt,
            add_eos=not add_generation_prompt,
        ))
        if max_length is not None and len(ids) > max_length:
            # Preserve generation prompt at the end if present
            if add_generation_prompt and ids[-1] == self.assistant_id:
                ids = ids[:max_length - 1] + [self.assistant_id]
            else:
                ids = ids[:max_length]
        return ids

    def pad_sequence(
        self,
        ids: list[int],
        max_length: int,
        padding_side: str = "right",
    ) -> tuple[list[int], list[int]]:
        """Return (padded_ids, attention_mask)."""
        length = len(ids)
        if length >= max_length:
            return ids[:max_length], [1] * max_length

        pad_count = max_length - length
        if padding_side == "right":
            padded = ids + [self.pad_id] * pad_count
            mask = [1] * length + [0] * pad_count
        else:
            padded = [self.pad_id] * pad_count + ids
            mask = [0] * pad_count + [1] * length
        return padded, mask

    def inspect(self) -> dict[str, Any]:
        return {
            "vocab_size": self.vocab_size,
            "pad_id": self.pad_id,
            "bos_id": self.bos_id,
            "eos_id": self.eos_id,
            "unk_id": self.unk_id,
            "fingerprint": self.fingerprint,
            "source_path": self._path,
        }


class TokenizerRegistry:
    """Registry maintaining canonical tokenizer instance."""

    _canonical: ProductionTokenizer | None = None

    @classmethod
    def get_canonical(cls, path: str | Path | None = None) -> ProductionTokenizer:
        if cls._canonical is not None and path is None:
            return cls._canonical

        tok_path = path or "artifacts/tokenizer-production-65536.json"
        raw = load_tokenizer(tok_path)
        cls._canonical = ProductionTokenizer(raw, path=tok_path)
        return cls._canonical

    @classmethod
    def register_canonical(cls, tokenizer: ProductionTokenizer) -> None:
        cls._canonical = tokenizer


def validate_model_tokenizer(model: Any, tokenizer: ProductionTokenizer | Any) -> bool:
    """Validate model and tokenizer compatibility:
    1. Vocab size match
    2. Embedding layer match
    3. LM head match
    """
    tok_vocab = getattr(tokenizer, "vocab_size", None)
    if tok_vocab is None:
        raise TokenizerValidationError("Tokenizer has no vocab_size attribute")

    # Inspect model vocab / embedding
    model_vocab = getattr(model, "vocab_size", None)
    if model_vocab is not None and model_vocab != tok_vocab:
        raise TokenizerValidationError(
            f"Vocab size mismatch! Model={model_vocab}, Tokenizer={tok_vocab}"
        )

    # Check token embedding shape if present
    embed = getattr(model, "tok_embeddings", None) or getattr(model, "token_embedding", None)
    if embed is not None and hasattr(embed, "weight"):
        if embed.weight.shape[0] != tok_vocab:
            raise TokenizerValidationError(
                f"Embedding vocab dimension {embed.weight.shape[0]} != Tokenizer vocab {tok_vocab}"
            )

    # Check LM head shape if present
    lm_head = getattr(model, "lm_head", None) or getattr(model, "output", None)
    if lm_head is not None and hasattr(lm_head, "weight"):
        if lm_head.weight.shape[0] != tok_vocab:
            raise TokenizerValidationError(
                f"Output head dimension {lm_head.weight.shape[0]} != Tokenizer vocab {tok_vocab}"
            )

    return True
