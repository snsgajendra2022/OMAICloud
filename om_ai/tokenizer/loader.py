from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .byte_bpe import ByteBPETokenizer


def tokenizer_fingerprint(path: str | Path) -> str:
    """Stable SHA-256 of tokenizer JSON bytes for checkpoint binding."""
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def tokenizer_sha256(path: str | Path) -> str:
    """Alias for ``tokenizer_fingerprint`` (checkpoint / registry binding)."""
    return tokenizer_fingerprint(path)


class HFTokenizerAdapter:
    """Adapter exposing the OM tokenizer API over Hugging Face `tokenizers` JSON."""

    def __init__(self, tokenizer, *, source_path: str | Path | None = None):
        self._tok = tokenizer
        self._source_path = str(source_path) if source_path else None
        self._fingerprint: str | None = (
            tokenizer_fingerprint(source_path) if source_path else None
        )

    @property
    def vocab(self):
        return self._tok.get_vocab()

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    @property
    def merges(self):
        return []

    @property
    def fingerprint(self) -> str | None:
        return self._fingerprint

    def _id(self, token: str):
        return self._tok.token_to_id(token)

    @property
    def pad_id(self):
        v = self._id("<pad>")
        if v is None:
            raise ValueError("Tokenizer missing <pad>")
        return v

    @property
    def bos_id(self):
        v = self._id("<bos>")
        if v is None:
            raise ValueError("Tokenizer missing <bos>")
        return v

    @property
    def eos_id(self):
        v = self._id("<eos>")
        if v is None:
            raise ValueError("Tokenizer missing <eos>")
        return v

    @property
    def unk_id(self):
        v = self._id("<unk>")
        if v is None:
            raise ValueError("Tokenizer missing <unk>")
        return v

    @property
    def system_id(self):
        return self._id("<system>")

    @property
    def system_end_id(self):
        return self._id("</system>")

    @property
    def user_id(self):
        return self._id("<user>")

    @property
    def user_end_id(self):
        return self._id("</user>")

    @property
    def assistant_id(self):
        return self._id("<assistant>")

    @property
    def assistant_end_id(self):
        return self._id("</assistant>")

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False):
        ids = list(self._tok.encode(text, add_special_tokens=False).ids)
        if add_bos:
            ids.insert(0, self.bos_id)
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids):
        return self._tok.decode([int(x) for x in ids], skip_special_tokens=True)

    def token_bytes(self, token_id: int) -> bytes:
        """Best-effort UTF-8 bytes for a single token (streaming decode)."""
        piece = self._tok.decode([int(token_id)], skip_special_tokens=False)
        # Avoid emitting special-token literals into the stream.
        if piece.startswith("<") and piece.endswith(">") and len(piece) <= 32:
            return b""
        return piece.encode("utf-8", errors="replace")

    def encode_chat(self, messages, *, add_generation_prompt=False, add_eos=True):
        ids = [self.bos_id]
        roles = {
            "system": ("<system>", "</system>"),
            "user": ("<user>", "</user>"),
            "assistant": ("<assistant>", "</assistant>"),
        }
        for message in messages:
            role = str(message.get("role", "user")).lower()
            content = str(message.get("content", ""))
            open_name, close_name = roles.get(role, roles["user"])
            open_id = self._id(open_name)
            close_id = self._id(close_name)
            if open_id is None or close_id is None:
                raise ValueError(
                    f"Tokenizer missing required chat tokens: {open_name}, {close_name}"
                )
            ids.append(open_id)
            ids.extend(self.encode(content))
            ids.append(close_id)

        if add_generation_prompt:
            if self.assistant_id is None:
                raise ValueError("Tokenizer missing <assistant>")
            ids.append(self.assistant_id)
        elif add_eos:
            ids.append(self.eos_id)
        return ids

    def inspect(self) -> dict[str, Any]:
        required = [
            "<system>", "</system>",
            "<user>", "</user>",
            "<assistant>", "</assistant>",
        ]
        return {
            "backend": "huggingface-tokenizers",
            "vocab_size": self.vocab_size,
            "chat_tokens_available": all(self._id(t) is not None for t in required),
            "fingerprint": self._fingerprint,
            "source_path": self._source_path,
            "special_tokens": {
                t: self._id(t)
                for t in ["<pad>", "<bos>", "<eos>", "<unk>", *required]
            },
            "pad_id": self.pad_id,
            "bos_id": self.bos_id,
            "eos_id": self.eos_id,
            "unk_id": self.unk_id,
        }


def load_tokenizer(path):
    """Single entry: load OM ByteBPE JSON or Hugging Face tokenizer JSON.

    Returns an object with encode / decode / encode_chat / inspect / vocab_size
    and pad/bos/eos/unk ids. Chat inference with ``add_generation_prompt=True``
    ends with the opening ``<assistant>`` special id.
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    # OM legacy/custom tokenizer.
    if isinstance(data.get("vocab"), dict) and "merges" in data:
        tok = ByteBPETokenizer.load(p)
        tok._source_path = str(p)  # type: ignore[attr-defined]
        tok._fingerprint = tokenizer_fingerprint(p)  # type: ignore[attr-defined]
        return tok

    # Hugging Face tokenizers JSON normally has a top-level model object.
    if isinstance(data.get("model"), dict):
        try:
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise RuntimeError(
                "This tokenizer requires the `tokenizers` package. "
                "Install it with: python3 -m pip install -U tokenizers"
            ) from exc

        tok = HFTokenizerAdapter(Tokenizer.from_file(str(p)), source_path=p)
        info = tok.inspect()

        if not info["chat_tokens_available"]:
            raise ValueError(
                "Production tokenizer loads, but OM chat special tokens are missing."
            )
        return tok

    raise ValueError(
        f"Unsupported tokenizer JSON format: {p}. "
        "Expected OM ByteBPE JSON or Hugging Face tokenizers JSON."
    )
