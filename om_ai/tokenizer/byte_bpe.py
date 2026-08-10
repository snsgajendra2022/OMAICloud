from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re


SPECIAL_TOKENS = [
    "<pad>", "<bos>", "<eos>", "<unk>",
    "<system>", "</system>",
    "<user>", "</user>",
    "<assistant>", "</assistant>",
]

_TOKENIZER_VERSION = "0.3.1"


def _byte_symbol(b: int) -> str:
    return f"<0x{b:02X}>"


@dataclass
class ByteBPETokenizer:
    vocab: dict[str, int]
    merges: list[tuple[str, str]]

    @classmethod
    def base(cls) -> "ByteBPETokenizer":
        vocab = {t: i for i, t in enumerate(SPECIAL_TOKENS)}
        for b in range(256):
            vocab[_byte_symbol(b)] = len(vocab)
        return cls(vocab=vocab, merges=[])

    def _special_id(self, token: str) -> int | None:
        return self.vocab.get(token)

    @property
    def pad_id(self) -> int:
        return self.vocab["<pad>"]

    @property
    def bos_id(self) -> int:
        return self.vocab["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.vocab["<eos>"]

    @property
    def unk_id(self) -> int:
        return self.vocab["<unk>"]

    @property
    def system_id(self) -> int | None:
        return self._special_id("<system>")

    @property
    def system_end_id(self) -> int | None:
        return self._special_id("</system>")

    @property
    def user_id(self) -> int | None:
        return self._special_id("<user>")

    @property
    def user_end_id(self) -> int | None:
        return self._special_id("</user>")

    @property
    def assistant_id(self) -> int | None:
        return self._special_id("<assistant>")

    @property
    def assistant_end_id(self) -> int | None:
        return self._special_id("</assistant>")

    def _initial_symbols(self, text: str) -> list[str]:
        return [_byte_symbol(b) for b in text.encode("utf-8")]

    def _apply_merges(self, symbols: list[str]) -> list[str]:
        for a, b in self.merges:
            merged = a + b
            out = []
            i = 0
            while i < len(symbols):
                if i + 1 < len(symbols) and symbols[i] == a and symbols[i + 1] == b:
                    out.append(merged)
                    i += 2
                else:
                    out.append(symbols[i])
                    i += 1
            symbols = out
        return symbols

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False) -> list[int]:
        ids: list[int] = []
        if add_bos:
            ids.append(self.bos_id)
        symbols = self._apply_merges(self._initial_symbols(text))
        ids.extend(self.vocab.get(s, self.unk_id) for s in symbols)
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def token_bytes(self, token_id: int) -> bytes:
        inv = {v: k for k, v in self.vocab.items()}
        sym = inv.get(int(token_id), "<unk>")
        if sym in set(SPECIAL_TOKENS):
            return b""
        raw = bytearray()
        for hx in re.findall(r"<0x([0-9A-F]{2})>", sym):
            raw.append(int(hx, 16))
        return bytes(raw)

    def decode(self, ids: list[int]) -> str:
        raw = bytearray()
        for idx in ids:
            raw.extend(self.token_bytes(int(idx)))
        return bytes(raw).decode("utf-8", errors="replace")

    def encode_chat(
        self,
        messages: list[dict],
        *,
        add_generation_prompt: bool = False,
        add_eos: bool = True,
    ) -> list[int]:
        ids: list[int] = [self.bos_id]
        role_tokens = {
            "system": ("<system>", "</system>"),
            "user": ("<user>", "</user>"),
            "assistant": ("<assistant>", "</assistant>"),
        }

        for msg in messages:
            role = str(msg.get("role", "user")).lower()
            content = str(msg.get("content", ""))
            open_name, close_name = role_tokens.get(role, role_tokens["user"])
            open_tok = self._special_id(open_name)
            close_tok = self._special_id(close_name)

            if open_tok is None or close_tok is None:
                ids.extend(self.encode(f"{open_name}\n{content}\n{close_name}\n"))
            else:
                ids.append(open_tok)
                ids.extend(self.encode(content))
                ids.append(close_tok)

        if add_generation_prompt:
            if self.assistant_id is None:
                ids.extend(self.encode("<assistant>\n"))
            else:
                ids.append(self.assistant_id)
        elif add_eos:
            ids.append(self.eos_id)

        return ids

    def inspect(self) -> dict:
        present_specials = [t for t in SPECIAL_TOKENS if t in self.vocab]
        return {
            "version": _TOKENIZER_VERSION,
            "vocab_size": len(self.vocab),
            "num_merges": len(self.merges),
            "special_tokens": present_specials,
            "chat_tokens_available": all(
                t in self.vocab
                for t in (
                    "<system>", "</system>",
                    "<user>", "</user>",
                    "<assistant>", "</assistant>",
                )
            ),
        }

    @classmethod
    def train(cls, texts: list[str], vocab_size: int = 1024, min_pair_freq: int = 2) -> "ByteBPETokenizer":
        tok = cls.base()
        if vocab_size <= len(tok.vocab):
            return tok
        corpus = [tok._initial_symbols(t) for t in texts if t]
        while len(tok.vocab) < vocab_size:
            pairs: Counter = Counter()
            for seq in corpus:
                pairs.update(zip(seq, seq[1:]))
            if not pairs:
                break
            (a, b), freq = pairs.most_common(1)[0]
            if freq < min_pair_freq:
                break
            merged = a + b
            if merged in tok.vocab:
                break
            tok.vocab[merged] = len(tok.vocab)
            tok.merges.append((a, b))
            new_corpus = []
            for seq in corpus:
                out, i = [], 0
                while i < len(seq):
                    if i + 1 < len(seq) and seq[i] == a and seq[i + 1] == b:
                        out.append(merged)
                        i += 2
                    else:
                        out.append(seq[i])
                        i += 1
                new_corpus.append(out)
            corpus = new_corpus
        return tok

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _TOKENIZER_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "special_tokens": [t for t in SPECIAL_TOKENS if t in self.vocab],
            "vocab": self.vocab,
            "merges": self.merges,
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, *, extend_specials: bool = False) -> "ByteBPETokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        vocab = {k: int(v) for k, v in data["vocab"].items()}
        merges = [tuple(x) for x in data["merges"]]
        tok = cls(vocab=vocab, merges=merges)

        if extend_specials:
            next_id = max(vocab.values()) + 1 if vocab else 0
            for token in SPECIAL_TOKENS:
                if token not in tok.vocab:
                    tok.vocab[token] = next_id
                    next_id += 1
        return tok
