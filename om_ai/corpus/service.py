"""
OM AI Corpus Service.

Handles importing, validating, deduplicating, and auditing text corpora
for model training.  Designed to be called by the CLI (``om-ai corpus``)
or directly from training pipeline scripts.

Features:
  - Source manifest ingestion (file paths or text)
  - PII filtering (email, phone, SSN-like patterns)
  - Language heuristic (ASCII ratio)
  - Near-duplicate detection via shingling + MinHash (simplified)
  - Exact-duplicate detection (SHA-256)
  - Contamination check against evaluation prompt file
  - Sharding into fixed-size output files
  - Audit trail JSON
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import struct
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PII patterns
# ─────────────────────────────────────────────────────────────────────────────

_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("email",   re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("phone",   re.compile(r"(?<!\d)(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")),
    ("ssn",     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ \-]?){13,16}\b")),
    ("ip_addr", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def _scrub_pii(text: str) -> tuple[str, list[str]]:
    """Remove PII patterns and return (scrubbed_text, list_of_hit_types)."""
    hits: list[str] = []
    for name, pat in _PII_PATTERNS:
        if pat.search(text):
            hits.append(name)
            text = pat.sub(f"[{name.upper()}_REDACTED]", text)
    return text, hits


# ─────────────────────────────────────────────────────────────────────────────
# Language heuristic
# ─────────────────────────────────────────────────────────────────────────────


def _detect_language(text: str, sample_size: int = 512) -> str:
    """Very lightweight language heuristic based on script distribution.

    Returns one of: ``"en"`` (high ASCII), ``"unicode"`` (non-ASCII dominant),
    or ``"mixed"``.  Not a substitute for a real LangID model.
    """
    sample = text[:sample_size]
    if not sample:
        return "unknown"
    ascii_count = sum(1 for c in sample if ord(c) < 128 and c.isprintable())
    ratio = ascii_count / len(sample)
    if ratio > 0.90:
        return "en"
    if ratio < 0.40:
        return "unicode"
    return "mixed"


# ─────────────────────────────────────────────────────────────────────────────
# Near-duplicate detection (simplified MinHash)
# ─────────────────────────────────────────────────────────────────────────────

_SHINGLE_SIZE = 5        # character-level shingles
_MINHASH_PERMS = 64      # number of hash permutations
_MAX_UINT32 = 0xFFFF_FFFF

# Pre-compute (a, b) pairs for _MINHASH_PERMS independent hash functions.
# Using a simple universal hash: h(x) = (a*x + b) mod p mod 2^32
_PRIME = 4_294_967_311   # next prime after 2^32
import random as _random
_rng = _random.Random(0xDEADBEEF)
_HASH_PARAMS: list[tuple[int, int]] = [
    (_rng.randint(1, _PRIME - 1), _rng.randint(0, _PRIME - 1))
    for _ in range(_MINHASH_PERMS)
]


def _minhash(text: str) -> tuple[int, ...]:
    """Compute a MinHash signature for *text* (character-level shingles)."""
    text = unicodedata.normalize("NFKC", text.lower())
    shingles: set[int] = set()
    for i in range(len(text) - _SHINGLE_SIZE + 1):
        shingle = text[i: i + _SHINGLE_SIZE]
        shingles.add(hash(shingle) & _MAX_UINT32)
    if not shingles:
        shingles = {hash(text) & _MAX_UINT32}

    sig: list[int] = []
    for a, b in _HASH_PARAMS:
        min_val = min(((a * s + b) % _PRIME) & _MAX_UINT32 for s in shingles)
        sig.append(min_val)
    return tuple(sig)


def _jaccard_estimate(sig_a: tuple[int, ...], sig_b: tuple[int, ...]) -> float:
    """Estimate Jaccard similarity from two MinHash signatures."""
    matches = sum(1 for x, y in zip(sig_a, sig_b) if x == y)
    return matches / _MINHASH_PERMS


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ImportResult:
    """Result of importing a single source."""
    source_id: str
    path: str
    accepted: bool
    reject_reason: str | None
    char_count: int
    language: str
    pii_hits: list[str]
    exact_dup: bool
    near_dup: bool
    near_dup_of: str | None
    sha256: str


@dataclass
class CorpusStats:
    """Aggregated statistics after an import run."""
    total_sources: int = 0
    accepted: int = 0
    rejected: int = 0
    exact_dups: int = 0
    near_dups: int = 0
    pii_scrubbed: int = 0
    total_chars: int = 0
    shards_written: int = 0
    languages: dict = field(default_factory=dict)
    audit: list[ImportResult] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# CorpusService
# ─────────────────────────────────────────────────────────────────────────────


class CorpusService:
    """Import, validate, deduplicate, and shard text corpora.

    Args:
        output_dir: Directory where shards are written.
        shard_size: Target number of characters per shard file.
        min_doc_chars: Reject documents shorter than this.
        near_dup_threshold: Jaccard similarity above which a document is
            considered a near-duplicate (0.8 is conservative).
        scrub_pii: Whether to redact PII before writing shards.
        eval_prompts_path: Optional path to a JSONL file of evaluation
            prompts; if provided, documents that contain evaluation prompt
            text verbatim are rejected (contamination check).
    """

    def __init__(
        self,
        output_dir: str | Path = "artifacts/corpus",
        shard_size: int = 5_000_000,
        min_doc_chars: int = 64,
        near_dup_threshold: float = 0.8,
        scrub_pii: bool = True,
        eval_prompts_path: str | Path | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shard_size = shard_size
        self.min_doc_chars = min_doc_chars
        self.near_dup_threshold = near_dup_threshold
        self.scrub_pii = scrub_pii

        # State
        self._seen_hashes: set[str] = set()          # exact dup detection
        self._minhash_sigs: list[tuple[str, tuple[int, ...]]] = []  # (id, sig)
        self._shard_buffer: list[str] = []
        self._shard_buffer_chars: int = 0
        self._shard_index: int = 0

        # Load eval prompts for contamination check
        self._eval_prompts: list[str] = []
        if eval_prompts_path:
            self._load_eval_prompts(eval_prompts_path)

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #

    def import_source(self, manifest_entry: dict, path: str | None = None) -> ImportResult:
        """Import a single source from a manifest entry.

        The manifest entry should be a dict with at least::

            {"id": "...", "path": "...", "format": "txt"}

        or::

            {"id": "...", "text": "..."}

        Args:
            manifest_entry: Dict describing the source.
            path: Override the path from the manifest entry.

        Returns:
            An ``ImportResult`` describing whether the document was accepted.
        """
        source_id = manifest_entry.get("id", hashlib.sha256(str(manifest_entry).encode()).hexdigest()[:16])
        file_path = path or manifest_entry.get("path", "")

        # Load text
        if file_path and Path(file_path).exists():
            try:
                text = Path(file_path).read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                return ImportResult(
                    source_id=source_id, path=file_path, accepted=False,
                    reject_reason=f"read_error:{exc}",
                    char_count=0, language="unknown", pii_hits=[],
                    exact_dup=False, near_dup=False, near_dup_of=None,
                    sha256="",
                )
        elif "text" in manifest_entry:
            text = manifest_entry["text"]
        else:
            return ImportResult(
                source_id=source_id, path=file_path, accepted=False,
                reject_reason="no_text_or_path",
                char_count=0, language="unknown", pii_hits=[],
                exact_dup=False, near_dup=False, near_dup_of=None,
                sha256="",
            )

        result = self._process_document(source_id, file_path or "(inline)", text)
        return result

    def import_many(self, manifest: list[dict]) -> CorpusStats:
        """Import all sources in *manifest* and return aggregate stats."""
        stats = CorpusStats(total_sources=len(manifest))
        for entry in manifest:
            result = self.import_source(entry)
            stats.audit.append(result)
            if result.accepted:
                stats.accepted += 1
                stats.total_chars += result.char_count
                lang = result.language
                stats.languages[lang] = stats.languages.get(lang, 0) + 1
            else:
                stats.rejected += 1
                if result.exact_dup:
                    stats.exact_dups += 1
                elif result.near_dup:
                    stats.near_dups += 1
            if result.pii_hits:
                stats.pii_scrubbed += 1
        stats.shards_written = self._flush_shards(final=True)
        return stats

    def validate(self, text: str) -> tuple[bool, str | None]:
        """Check whether *text* is valid for inclusion (length, language).

        Returns:
            ``(True, None)`` if valid; ``(False, reason)`` otherwise.
        """
        if len(text) < self.min_doc_chars:
            return False, f"too_short:{len(text)}<{self.min_doc_chars}"
        lang = _detect_language(text)
        return True, None

    def stats(self) -> dict:
        """Return current deduplication state summary."""
        return {
            "seen_exact": len(self._seen_hashes),
            "minhash_index_size": len(self._minhash_sigs),
            "shard_buffer_chars": self._shard_buffer_chars,
            "shards_written": self._shard_index,
        }

    def flush(self) -> int:
        """Force-write remaining buffer to a final shard. Returns shard count."""
        return self._flush_shards(final=True)

    # ------------------------------------------------------------------ #
    #  CLI-facing helpers                                                   #
    # ------------------------------------------------------------------ #

    def import_path(
        self,
        path: str | Path,
        *,
        license: str = "proprietary-owned",
        owner: str = "om-ai",
        source_id: str = "import-1",
    ) -> dict:
        """Import a file path for CLI `om-ai corpus import`."""
        p = Path(path)
        result = self.import_source(
            {
                "id": source_id,
                "path": str(p),
                "license": license,
                "owner": owner,
                "allowed_for_training": True,
            }
        )
        self.flush()
        return asdict(result)

    def validate_manifest(self, manifest_path: str | Path) -> dict:
        """Validate a source manifest via CorpusGovernance rules."""
        from om_ai.data.governance import CorpusGovernance

        items = CorpusGovernance.load_manifest(manifest_path)
        return {"ok": True, "sources": len(items), "ids": [i.source_id for i in items]}

    def dedupe(self, input_path: str | Path, output_path: str | Path) -> dict:
        """Exact-dedupe a text or JSONL corpus file to output."""
        from om_ai.data.pipeline import DatasetPipeline

        pipe = DatasetPipeline()
        records = pipe.process(DatasetPipeline.load(input_path))
        DatasetPipeline.save_jsonl(records, output_path)
        return {"input": str(input_path), "output": str(output_path), "records": len(records)}

    def audit(self, input_path: str | Path, output_path: str | Path) -> dict:
        """Write an audit JSON for a corpus file."""
        from om_ai.data.pipeline import DatasetPipeline
        from om_ai.data.governance import CorpusGovernance
        from hashlib import sha256

        records = DatasetPipeline().process(DatasetPipeline.load(input_path))
        rows = []
        for r in records:
            rows.append(
                {
                    "source": r.source,
                    "license": r.license,
                    "quality_score": r.quality_score,
                    "chars": len(r.text),
                    "content_hash": sha256(r.text.encode()).hexdigest(),
                    "language": r.language,
                }
            )
        CorpusGovernance.write_audit(rows, output_path)
        return {"records": len(rows), "audit": str(output_path)}

    def shard(self, input_path: str | Path, output_dir: str | Path, shard_size: int = 1000) -> dict:
        """Shard a corpus into JSONL files of *shard_size* documents."""
        from om_ai.data.pipeline import DatasetPipeline

        records = DatasetPipeline().process(DatasetPipeline.load(input_path))
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        written = []
        for i in range(0, max(1, len(records)), max(1, shard_size)):
            chunk = records[i : i + shard_size]
            target = out / f"shard-{i // max(1, shard_size):05d}.jsonl"
            DatasetPipeline.save_jsonl(chunk, target)
            written.append(str(target))
        return {"shards": written, "records": len(records)}

    def file_stats(self, input_path: str | Path) -> dict:
        """Corpus statistics for a single input file."""
        from om_ai.data.pipeline import DatasetPipeline

        records = DatasetPipeline().process(DatasetPipeline.load(input_path))
        chars = sum(len(r.text) for r in records)
        return {
            "path": str(input_path),
            "documents": len(records),
            "chars": chars,
            "avg_chars": round(chars / max(1, len(records)), 2),
            "licenses": sorted({r.license for r in records}),
        }

    # ------------------------------------------------------------------ #
    #  Internal document processing                                         #
    # ------------------------------------------------------------------ #

    def _process_document(self, source_id: str, path: str, text: str) -> ImportResult:
        sha = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        pii_hits: list[str] = []

        # Length check
        if len(text) < self.min_doc_chars:
            return ImportResult(
                source_id=source_id, path=path, accepted=False,
                reject_reason=f"too_short:{len(text)}",
                char_count=len(text), language=_detect_language(text),
                pii_hits=[], exact_dup=False, near_dup=False, near_dup_of=None,
                sha256=sha,
            )

        # Exact duplicate
        if sha in self._seen_hashes:
            return ImportResult(
                source_id=source_id, path=path, accepted=False,
                reject_reason="exact_duplicate",
                char_count=len(text), language=_detect_language(text),
                pii_hits=[], exact_dup=True, near_dup=False, near_dup_of=None,
                sha256=sha,
            )

        # Near duplicate
        sig = _minhash(text)
        near_dup_of: str | None = None
        for prev_id, prev_sig in self._minhash_sigs:
            if _jaccard_estimate(sig, prev_sig) >= self.near_dup_threshold:
                near_dup_of = prev_id
                break
        if near_dup_of:
            return ImportResult(
                source_id=source_id, path=path, accepted=False,
                reject_reason=f"near_duplicate_of:{near_dup_of}",
                char_count=len(text), language=_detect_language(text),
                pii_hits=[], exact_dup=False, near_dup=True, near_dup_of=near_dup_of,
                sha256=sha,
            )

        # Contamination check
        if self._is_contaminated(text):
            return ImportResult(
                source_id=source_id, path=path, accepted=False,
                reject_reason="eval_contamination",
                char_count=len(text), language=_detect_language(text),
                pii_hits=[], exact_dup=False, near_dup=False, near_dup_of=None,
                sha256=sha,
            )

        # PII scrub
        if self.scrub_pii:
            text, pii_hits = _scrub_pii(text)

        lang = _detect_language(text)

        # Accept
        self._seen_hashes.add(sha)
        self._minhash_sigs.append((source_id, sig))
        self._shard_buffer.append(text)
        self._shard_buffer_chars += len(text)
        if self._shard_buffer_chars >= self.shard_size:
            self._flush_shards(final=False)

        return ImportResult(
            source_id=source_id, path=path, accepted=True,
            reject_reason=None,
            char_count=len(text), language=lang,
            pii_hits=pii_hits, exact_dup=False, near_dup=False, near_dup_of=None,
            sha256=sha,
        )

    # ------------------------------------------------------------------ #
    #  Sharding                                                             #
    # ------------------------------------------------------------------ #

    def _flush_shards(self, final: bool = False) -> int:
        """Write buffered text to a shard file. Returns total shards written."""
        if not self._shard_buffer:
            return self._shard_index
        shard_path = self.output_dir / f"shard_{self._shard_index:05d}.jsonl"
        with shard_path.open("w", encoding="utf-8") as fh:
            for doc in self._shard_buffer:
                fh.write(json.dumps({"text": doc}, ensure_ascii=False) + "\n")
        logger.info(
            "Wrote shard %d: %d docs, %d chars → %s",
            self._shard_index, len(self._shard_buffer),
            self._shard_buffer_chars, shard_path,
        )
        self._shard_index += 1
        self._shard_buffer = []
        self._shard_buffer_chars = 0
        return self._shard_index

    # ------------------------------------------------------------------ #
    #  Contamination check                                                  #
    # ------------------------------------------------------------------ #

    def _load_eval_prompts(self, path: str | Path) -> None:
        path = Path(path)
        if not path.exists():
            logger.warning("eval_prompts_path %s does not exist — skipping", path)
            return
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                prompt = obj.get("prompt") or obj.get("text") or obj.get("input") or ""
                if prompt:
                    self._eval_prompts.append(prompt.strip().lower())
            except json.JSONDecodeError:
                self._eval_prompts.append(line.lower())
        logger.info("Loaded %d eval prompts for contamination check", len(self._eval_prompts))

    def _is_contaminated(self, text: str) -> bool:
        if not self._eval_prompts:
            return False
        text_lower = text.lower()
        for prompt in self._eval_prompts:
            if len(prompt) >= 32 and prompt in text_lower:
                return True
        return False
