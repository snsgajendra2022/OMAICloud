from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Iterator
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
            most = Counter(words).most_common(1)[0][1] if words else 0
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
    def iter_load(path: str | Path) -> Iterator[DocumentRecord]:
        """Stream documents line-by-line / blank-line blocks. Never ``read_text()`` whole file."""
        p = Path(path)
        if p.suffix.lower() == ".jsonl":
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    text = obj.get("text")
                    if text is None:
                        continue
                    yield DocumentRecord(
                        text=str(text),
                        source=obj.get("source", str(p)),
                        license=obj.get("license", "unknown"),
                        quality_score=float(obj.get("quality_score", 0.5)),
                        category=obj.get("category", "general"),
                        language=obj.get("language", "und"),
                        version=str(obj.get("version", "1")),
                    )
            return

        # Plain text: split on blank lines when the file is multi-document
        # (e.g. FineWeb dumps). A single contiguous blob stays one record.
        license = "unknown"
        source = str(p)
        version = "1"
        cand = p.parent / f"{p.stem}.manifest.json"
        if cand.is_file():
            try:
                with cand.open("r", encoding="utf-8") as mf:
                    meta_obj = json.load(mf)
                license = str(meta_obj.get("license", license))
                source = str(meta_obj.get("source", source))
                version = str(meta_obj.get("config", meta_obj.get("version", version)))
            except Exception:
                pass

        buf: list[str] = []
        yielded = False

        def flush() -> DocumentRecord | None:
            text = "\n".join(buf).strip()
            buf.clear()
            if not text:
                return None
            return DocumentRecord(
                text=text,
                source=source,
                license=license,
                version=version,
            )

        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    rec = flush()
                    if rec is not None:
                        yielded = True
                        yield rec
                else:
                    buf.append(line.rstrip("\n"))
            rec = flush()
            if rec is not None:
                yielded = True
                yield rec

        if not yielded:
            yield DocumentRecord(text="", source=source, license=license, version=version)

    @staticmethod
    def load(path: str | Path) -> list[DocumentRecord]:
        return list(DatasetPipeline.iter_load(path))

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

    def iter_process(self, records: Iterable[DocumentRecord]) -> Iterator[DocumentRecord]:
        """Streaming clean/dedupe — same rules as ``process`` without materializing all rows."""
        seen: set[str] = set()
        for rec in records:
            text = self.clean(rec.text)
            if len(text) < self.min_chars or not self.safe_enough(text):
                continue
            new = DocumentRecord(**{**asdict(rec), "text": text, "quality_score": self.quality_score(text)})
            fp = new.fingerprint()
            if fp in seen:
                continue
            seen.add(fp)
            yield new

    @staticmethod
    def tokenize_streaming(
        records: Iterable[DocumentRecord],
        tokenizer,
        *,
        add_eos: bool = True,
        max_tokens: int | None = None,
        max_docs: int | None = None,
    ) -> list[int]:
        """Tokenize incrementally; stop once ``max_tokens`` / ``max_docs`` reached."""
        ids: list[int] = []
        docs = 0
        for r in records:
            ids.extend(tokenizer.encode(r.text, add_eos=add_eos))
            docs += 1
            if max_docs is not None and docs >= max_docs:
                break
            if max_tokens is not None and len(ids) >= max_tokens:
                ids = ids[:max_tokens]
                break
        return ids