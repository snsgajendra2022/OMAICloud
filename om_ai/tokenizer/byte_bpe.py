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

# Tokens present in old tokenizers saved before the chat specials were added.
_LEGACY_SPECIAL_TOKENS = ["<pad>", "<bos>", "<eos>", "<unk>"]

_TOKENIZER_VERSION = "0.3.0"


def _byte_symbol(b: int) -> str:
    return f"<0x{b:02X}>"


@dataclass
class ByteBPETokenizer:
    vocab: dict[str, int]
    merges: list[tuple[str, str]]

    # ------------------------------------------------------------------ #
    #  Factory                                                              #
    # ------------------------------------------------------------------ #

    @classmethod
    def base(cls) -> "ByteBPETokenizer":
        vocab = {t: i for i, t in enumerate(SPECIAL_TOKENS)}
        for b in range(256):
            vocab[_byte_symbol(b)] = len(vocab)
        return cls(vocab=vocab, merges=[])

    # ------------------------------------------------------------------ #
    #  Special-token id properties                                          #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    #  Core encode / decode                                                 #
    # ------------------------------------------------------------------ #

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

    def decode(self, ids: list[int]) -> str:
        inv = {v: k for k, v in self.vocab.items()}
        # All known special tokens (not just the original four)
        all_specials = set(SPECIAL_TOKENS)
        raw = bytearray()
        for idx in ids:
            sym = inv.get(int(idx), "<unk>")
            if sym in all_specials:
                continue
            for hx in re.findall(r"<0x([0-9A-F]{2})>", sym):
                raw.append(int(hx, 16))
        return raw.decode("utf-8", errors="replace")

    # ------------------------------------------------------------------ #
    #  Chat encoding                                                        #
    # ------------------------------------------------------------------ #

    def encode_chat(
        self,
        messages: list[dict],
        *,
        add_generation_prompt: bool = False,
        add_eos: bool | None = None,
    ) -> list[int]:
        """Encode chat messages into a flat token-id sequence.

        Each message dict must have ``role`` (system | user | assistant) and
        ``content`` (str).  Role wrappers use dedicated special-token IDs when
        present (never byte-encoded angle-bracket text).

        Training / completed dialogue (default)::

            <bos><system>…</system><user>…</user><assistant>…</assistant><eos>

        Inference prompt (``add_generation_prompt=True``)::

            <bos><system>…</system><user>…</user><assistant>
                                                      ↑ generation starts here

        When ``add_eos`` is omitted it defaults to ``not add_generation_prompt``.
        Falls back gracefully if chat special tokens are missing (legacy vocab).
        """
        if add_eos is None:
            add_eos = not add_generation_prompt

        ids: list[int] = [self.bos_id]
        for msg in messages:
            role = str(msg.get("role", "user")).lower()
            content = msg.get("content", "")
            if content is None:
                content = ""
            elif not isinstance(content, str):
                content = str(content)

            if role == "system":
                open_tok = self._special_id("<system>")
                close_tok = self._special_id("</system>")
            elif role == "assistant":
                open_tok = self._special_id("<assistant>")
                close_tok = self._special_id("</assistant>")
            else:
                open_tok = self._special_id("<user>")
                close_tok = self._special_id("</user>")

            if open_tok is not None:
                ids.append(open_tok)
            ids.extend(self.encode(content))
            if close_tok is not None:
                ids.append(close_tok)

        if add_generation_prompt:
            open_asst = self._special_id("<assistant>")
            if open_asst is not None:
                ids.append(open_asst)
        elif add_eos:
            ids.append(self.eos_id)
        return ids

    # ------------------------------------------------------------------ #
    #  Introspection                                                        #
    # ------------------------------------------------------------------ #

    def inspect(self) -> dict:
        """Return a summary dict describing this tokenizer."""
        present_specials = [t for t in SPECIAL_TOKENS if t in self.vocab]
        return {
            "version": _TOKENIZER_VERSION,
            "vocab_size": len(self.vocab),
            "num_merges": len(self.merges),
            "special_tokens": present_specials,
            "chat_tokens_available": all(
                t in self.vocab
                for t in ("<system>", "<user>", "<assistant>")
            ),
        }

    # ------------------------------------------------------------------ #
    #  Training                                                             #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    #  Persistence                                                          #
    # ------------------------------------------------------------------ #

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _TOKENIZER_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "special_tokens": [t for t in SPECIAL_TOKENS if t in self.vocab],
            "vocab": self.vocab,
            "merges": self.merges,
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: str | Path, *, extend_specials: bool = False) -> "ByteBPETokenizer":
        data = json.loads(Path(path).read_text())
        vocab: dict[str, int] = {k: int(v) for k, v in data["vocab"].items()}
        merges: list[tuple[str, str]] = [tuple(x) for x in data["merges"]]  # type: ignore[misc]
        tok = cls(vocab=vocab, merges=merges)

        # Optional: auto-extend with chat specials (disabled by default so
        # existing checkpoints keep matching vocab sizes).
        if extend_specials:
            next_id = max(vocab.values()) + 1 if vocab else 0
            extended = False
            for token in SPECIAL_TOKENS:
                if token not in tok.vocab:
                    tok.vocab[token] = next_id
                    next_id += 1
                    extended = True
            if extended:
                import warnings
                warnings.warn(
                    "Loaded tokenizer is missing new special tokens — they have been "
                    "appended at the end of the vocabulary. Re-save to persist this.",
                    stacklevel=2,
                )
        return tok
