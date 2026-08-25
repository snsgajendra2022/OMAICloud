"""Document ingestion: load → clean → chunk → metadata."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DocumentMeta:
    title: str
    domain: str
    year: str = ""
    topics: list[str] = field(default_factory=list)
    source_path: str = ""
    doc_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "domain": self.domain,
            "year": self.year,
            "topics": self.topics,
            "source_path": self.source_path,
            "doc_id": self.doc_id,
        }


def guess_domain(path: Path, text: str) -> str:
    name = (path.stem + " " + text[:500]).lower()
    for key, dom in (
        ("physics", "physics"),
        ("math", "mathematics"),
        ("chem", "chemistry"),
        ("bio", "biology"),
        ("medic", "medicine"),
        ("histor", "history"),
        ("business", "business"),
        ("python", "programming"),
        ("react", "programming"),
        ("engineer", "engineering"),
        ("patent", "patents"),
    ):
        if key in name:
            return dom
    return "general"


def extract_topics(text: str, *, k: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text.lower())
    stop = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "were",
        "which",
        "their",
        "about",
        "would",
        "there",
        "could",
        "other",
        "into",
        "than",
        "then",
        "them",
        "these",
        "those",
        "also",
        "more",
        "some",
        "such",
        "only",
        "over",
        "after",
        "when",
        "what",
        "your",
        "will",
        "each",
        "make",
        "like",
        "just",
        "over",
    }
    freq: dict[str, int] = {}
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:k]]


def load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown", ".csv", ".json", ".html", ".htm", ".py", ".ts", ".js"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            import pypdf  # type: ignore

            reader = pypdf.PdfReader(str(path))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            return f"[pdf unreadable without pypdf: {path.name}]"
    if suffix == ".docx":
        try:
            import docx  # type: ignore

            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs)
        except Exception:
            return f"[docx unreadable without python-docx: {path.name}]"
    return path.read_text(encoding="utf-8", errors="ignore")


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, *, size: int = 800, overlap: int = 100) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        chunks.append(text[i : i + size])
        i += max(1, size - overlap)
    return chunks


def build_metadata(path: Path, text: str) -> DocumentMeta:
    year_m = re.search(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", text[:2000] + " " + path.name)
    doc_id = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:16]
    return DocumentMeta(
        title=path.stem.replace("_", " ").replace("-", " ").title(),
        domain=guess_domain(path, text),
        year=year_m.group(1) if year_m else "",
        topics=extract_topics(text),
        source_path=str(path),
        doc_id=doc_id,
    )


def ingest_file(path: str | Path, *, out_root: str | Path | None = None) -> dict[str, Any]:
    path = Path(path)
    raw = load_text(path)
    cleaned = clean_text(raw)
    meta = build_metadata(path, cleaned)
    chunks = chunk_text(cleaned)
    result = {
        "metadata": meta.to_dict(),
        "chunk_count": len(chunks),
        "char_count": len(cleaned),
        "chunks_preview": chunks[:2],
    }
    if out_root:
        root = Path(out_root)
        for sub in ("processed", "chunks", "metadata", "embeddings"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        (root / "processed" / f"{meta.doc_id}.txt").write_text(cleaned, encoding="utf-8")
        (root / "metadata" / f"{meta.doc_id}.json").write_text(
            json.dumps(meta.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        (root / "chunks" / f"{meta.doc_id}.jsonl").write_text(
            "\n".join(json.dumps({"doc_id": meta.doc_id, "i": i, "text": c}) for i, c in enumerate(chunks))
            + ("\n" if chunks else ""),
            encoding="utf-8",
        )
        result["stored_under"] = str(root)
    return result
