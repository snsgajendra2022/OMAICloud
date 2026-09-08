"""Production-grade custom BPE tokenizer for OM conversational datasets."""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

_WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
_SPECIAL_SPLIT = re.compile(
    r"(<\|pad\|>|<\|eos\|>|<\|user\|>|<\|assistant\|>|<\|thought\|>|<\|final_response\|>)"
)


class OMTokenizer:
    def __init__(self, vocab_size: int = 8000):
        self.vocab_size = int(vocab_size)
        self.special_tokens = [
            "<|pad|>",
            "<|eos|>",
            "<|user|>",
            "<|assistant|>",
            "<|thought|>",
            "<|final_response|>",
        ]
        self.encoder: dict[str, int] = {}
        self.decoder: dict[int, str] = {}
        self.merges: list[tuple[str, str]] = []

    def train(self, file_path: str, *, max_chars: int = 5_000_000, max_words: int = 120_000) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Training corpus not found at {file_path}. Please create the file."
            )

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read(max_chars)

        print("Tokenizer: Slicing text structural frequencies...")
        unique_chars = sorted(set(text))
        vocab = list(self.special_tokens)
        for ch in unique_chars:
            if ch not in vocab:
                vocab.append(ch)
        self.encoder = {t: i for i, t in enumerate(vocab)}
        self.merges = []
        protected = set(self.special_tokens)

        words = Counter(_WORD_RE.findall(text))
        if len(words) > max_words:
            words = Counter(dict(words.most_common(max_words)))
        splits = {w: list(w) for w in words}

        while len(self.encoder) < self.vocab_size:
            pairs: dict[tuple[str, str], int] = defaultdict(int)
            for w, freq in words.items():
                split = splits[w]
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
                break
            self.encoder[new_token] = len(self.encoder)
            self.merges.append(best_pair)
            for w in words:
                split = splits[w]
                i = 0
                while i < len(split) - 1:
                    if split[i] == best_pair[0] and split[i + 1] == best_pair[1]:
                        split[i : i + 2] = [new_token]
                    else:
                        i += 1

        self.decoder = {i: token for token, i in self.encoder.items()}
        out = Path(__file__).resolve().parent / "om_tokenizer.json"
        self.save(out)
        print(f"Tokenizer configuration successfully persisted to '{out}'")

    def save(self, path: str | Path | None = None) -> None:
        path = Path(path or Path(__file__).resolve().parent / "om_tokenizer.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "vocab_size": self.vocab_size,
                    "encoder": self.encoder,
                    "merges": [list(m) for m in self.merges],
                    "special_tokens": self.special_tokens,
                    "decoder": {str(k): v for k, v in self.decoder.items()},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def load(self, path: str | Path | None = None) -> None:
        path = Path(path or Path(__file__).resolve().parent / "om_tokenizer.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.encoder = {str(k): int(v) for k, v in data["encoder"].items()}
        self.decoder = {int(k): v for k, v in data.get("decoder", {}).items()}
        if not self.decoder:
            self.decoder = {i: t for t, i in self.encoder.items()}
        self.merges = [tuple(m) for m in data.get("merges") or []]
        self.special_tokens = list(data.get("special_tokens") or self.special_tokens)
        self.vocab_size = int(data.get("vocab_size") or len(self.encoder))

    def encode(self, text: str) -> list[int]:
        tokens: list[int] = []
        for part in _SPECIAL_SPLIT.split(text):
            if not part:
                continue
            if part in self.encoder:
                tokens.append(self.encoder[part])
                continue
            for word in _WORD_RE.findall(part):
                if word in self.encoder:
                    tokens.append(self.encoder[word])
                    continue
                chars = list(word)
                for a, b in self.merges:
                    merged = a + b
                    i = 0
                    while i < len(chars) - 1:
                        if chars[i] == a and chars[i + 1] == b:
                            chars[i : i + 2] = [merged]
                        else:
                            i += 1
                for tok in chars:
                    tokens.append(self.encoder.get(tok, 0))
        return tokens

    def decode(self, ids: list[int]) -> str:
        return "".join(self.decoder.get(int(i), "") for i in ids)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    t = OMTokenizer(vocab_size=int(os.getenv("OM_VOCAB_SIZE", "4000")))
    t.train(str(here / "dataset.txt"))
