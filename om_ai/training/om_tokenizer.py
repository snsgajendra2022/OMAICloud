"""Self-contained BPE sub-word tokenizer for OM-1.0 (no Hugging Face).

Groups characters into meaningful pieces (e.g. learn + ing) so the model can
learn concepts instead of single letters. Chat specials:
``<|pad|>``, ``<|eos|>``, ``<|user|>``, ``<|assistant|>``.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


_WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class OMTokenizer:
    """Completely custom, self-contained sub-word tokenizer for OM-1.0."""

    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = int(vocab_size)
        self.encoder: dict[str, int] = {}
        self.decoder: dict[int, str] = {}
        self.merges: list[tuple[str, str]] = []
        self.special_tokens = [
            "<|pad|>",
            "<|eos|>",
            "<|user|>",
            "<|assistant|>",
            "<|thought|>",
        ]

    @property
    def pad_id(self) -> int:
        return self.encoder.get("<|pad|>", 0)

    @property
    def eos_id(self) -> int:
        return self.encoder.get("<|eos|>", 1)

    @property
    def user_id(self) -> int:
        return self.encoder.get("<|user|>", 2)

    @property
    def assistant_id(self) -> int:
        return self.encoder.get("<|assistant|>", 3)

    @property
    def thought_id(self) -> int:
        return self.encoder.get("<|thought|>", 4)

    def train_tokenizer(self, text_corpus: str, *, max_words: int = 200_000) -> None:
        print("Tokenizer is analyzing training text structures...")
        # Protect specials so BPE never merges across them incorrectly
        protected = set(self.special_tokens)
        unique_chars = sorted(set(ch for ch in text_corpus if ch not in "\x00"))
        vocab = list(self.special_tokens)
        for ch in unique_chars:
            if ch not in protected and ch not in vocab:
                vocab.append(ch)
        self.encoder = {word: i for i, word in enumerate(vocab)}
        self.merges = []

        words = Counter(_WORD_RE.findall(text_corpus))
        # Cap rare-word explosion on huge corpora (train on top-N by frequency)
        if len(words) > max_words:
            words = Counter(dict(words.most_common(max_words)))
        splits: dict[str, list[str]] = {
            word: [char for char in word] for word in words
        }

        while len(self.encoder) < self.vocab_size:
            pairs: dict[tuple[str, str], int] = defaultdict(int)
            for word, freq in words.items():
                split = splits[word]
                for i in range(len(split) - 1):
                    a, b = split[i], split[i + 1]
                    if a in protected or b in protected:
                        continue
                    pairs[(a, b)] += freq
            if not pairs:
                break
            best_pair = max(pairs, key=pairs.get)
            new_token = "".join(best_pair)
            if new_token in self.encoder:
                # Force progress by skipping already-known merges
                pairs.pop(best_pair, None)
                if not pairs:
                    break
                best_pair = max(pairs, key=pairs.get)
                new_token = "".join(best_pair)
                if new_token in self.encoder:
                    break
            self.encoder[new_token] = len(self.encoder)
            self.merges.append(best_pair)
            for word in words:
                split = splits[word]
                i = 0
                while i < len(split) - 1:
                    if split[i] == best_pair[0] and split[i + 1] == best_pair[1]:
                        split[i : i + 2] = [new_token]
                    else:
                        i += 1

        self.decoder = {i: token for token, i in self.encoder.items()}
        print(f"Tokenizer configuration complete. Vocabulary size: {len(self.encoder)}")

    def _encode_piece(self, piece: str) -> list[int]:
        if piece in self.encoder:
            return [self.encoder[piece]]
        # Greedy longest-match fallback over characters / merges
        chars = list(piece)
        # Apply learned merges in order
        for a, b in self.merges:
            i = 0
            merged = "".join((a, b))
            while i < len(chars) - 1:
                if chars[i] == a and chars[i + 1] == b:
                    chars[i : i + 2] = [merged]
                else:
                    i += 1
        ids: list[int] = []
        for tok in chars:
            if tok in self.encoder:
                ids.append(self.encoder[tok])
            else:
                for ch in tok:
                    ids.append(self.encoder.get(ch, self.pad_id))
        return ids

    def encode(self, text: str) -> list[int]:
        tokens: list[int] = []
        # Keep chat specials as atomic tokens when present in the stream
        parts = re.split(
            r"(<\|user\|>|<\|assistant\|>|<\|thought\|>|<\|eos\|>|<\|pad\|>)",
            text,
        )
        for part in parts:
            if not part:
                continue
            if part in self.encoder:
                tokens.append(self.encoder[part])
                continue
            for word in _WORD_RE.findall(part):
                tokens.extend(self._encode_piece(word))
        return tokens

    def decode(self, ids: list[int]) -> str:
        return "".join(self.decoder.get(int(idx), "") for idx in ids)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "vocab_size": self.vocab_size,
                    "encoder": self.encoder,
                    "merges": [list(m) for m in self.merges],
                    "special_tokens": self.special_tokens,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "OMTokenizer":
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        tok = cls(vocab_size=int(obj.get("vocab_size") or 5000))
        tok.encoder = {str(k): int(v) for k, v in obj["encoder"].items()}
        tok.merges = [tuple(m) for m in obj.get("merges") or []]
        tok.special_tokens = list(obj.get("special_tokens") or tok.special_tokens)
        tok.decoder = {i: t for t, i in tok.encoder.items()}
        return tok
