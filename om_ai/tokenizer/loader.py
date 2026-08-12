from __future__ import annotations

import json
from pathlib import Path

from .byte_bpe import ByteBPETokenizer


class HFTokenizerAdapter:
    """Adapter exposing the OM tokenizer API over Hugging Face `tokenizers` JSON."""

    def __init__(self, tokenizer):
        self._tok = tokenizer

    @property
    def vocab(self):
        return self._tok.get_vocab()

    @property
    def merges(self):
        return []

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

    def inspect(self):
        required = [
            "<system>", "</system>",
            "<user>", "</user>",
            "<assistant>", "</assistant>",
        ]
        return {
            "backend": "huggingface-tokenizers",
            "vocab_size": len(self.vocab),
            "chat_tokens_available": all(self._id(t) is not None for t in required),
            "special_tokens": {
                t: self._id(t)
                for t in ["<pad>", "<bos>", "<eos>", "<unk>", *required]
            },
        }


def load_tokenizer(path):
    """Load either OM legacy ByteBPE JSON or Hugging Face tokenizer JSON."""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    # OM legacy/custom tokenizer.
    if isinstance(data.get("vocab"), dict) and "merges" in data:
        return ByteBPETokenizer.load(p)

    # Hugging Face tokenizers JSON normally has a top-level model object.
    if isinstance(data.get("model"), dict):
        try:
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise RuntimeError(
                "This tokenizer requires the `tokenizers` package. "
                "Install it with: python3 -m pip install -U tokenizers"
            ) from exc

        tok = HFTokenizerAdapter(Tokenizer.from_file(str(p)))
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
