from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import json
import re
import unicodedata

from om_ai.tokenizer import ByteBPETokenizer


@dataclass(slots=True)
class DocumentRecord:
    text: str
    source: str = "unknown"
    license: str = "unknown"
    quality_score: float = 0.5
    category: str = "general"
    language: str = "und"
    version: str = "1"

    def fingerprint(self) -> str:
        return sha256(self.text.strip().encode("utf-8")).hexdigest()


class DatasetPipeline:
    def __init__(self, min_chars: int = 20, max_repetition_ratio: float = 0.35):
        self.min_chars = min_chars
        self.max_repetition_ratio = max_repetition_ratio

    def clean(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def quality_score(self, text: str) -> float:
        if not text:
            return 0.0
        printable = sum(ch.isprintable() or ch in "\n\t" for ch in text) / len(text)
        words = re.findall(r"\w+", text.lower())
        unique = len(set(words)) / max(1, len(words))
        length = min(1.0, len(text) / 1000)
        return round(0.5 * printable + 0.3 * unique + 0.2 * length, 4)

    def safe_enough(self, text: str) -> bool:
        # Dataset sanitation baseline: reject obvious secret material and extreme repetition.
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
            return False
        words = re.findall(r"\w+", text.lower())
        if len(words) > 50:
            most = max((words.count(w) for w in set(words)), default=0)
            if most / len(words) > self.max_repetition_ratio:
                return False
        return True

    def process(self, records: Iterable[DocumentRecord]) -> list[DocumentRecord]:
        seen = set()
        out = []
        for rec in records:
            text = self.clean(rec.text)
            if len(text) < self.min_chars or not self.safe_enough(text):
                continue
            new = DocumentRecord(**{**asdict(rec), "text": text, "quality_score": self.quality_score(text)})
            fp = new.fingerprint()
            if fp in seen:
                continue
            seen.add(fp)
            out.append(new)
        return out

    @staticmethod
    def load(path: str | Path) -> list[DocumentRecord]:
        p = Path(path)
        if p.suffix.lower() == ".jsonl":
            rows = []
            for line in p.read_text(errors="ignore").splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                rows.append(DocumentRecord(
                    text=obj["text"], source=obj.get("source", str(p)), license=obj.get("license", "unknown"),
                    quality_score=float(obj.get("quality_score", 0.5)), category=obj.get("category", "general"),
                    language=obj.get("language", "und"), version=str(obj.get("version", "1"))))
            return rows
        return [DocumentRecord(text=p.read_text(errors="ignore"), source=str(p))]

    @staticmethod
    def save_jsonl(records: Iterable[DocumentRecord], path: str | Path) -> None:
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    @staticmethod
    def tokenize(records: Iterable[DocumentRecord], tokenizer: ByteBPETokenizer, add_eos: bool = True) -> list[int]:
        ids: list[int] = []
        for r in records:
            ids.extend(tokenizer.encode(r.text, add_eos=add_eos))
        return ids
