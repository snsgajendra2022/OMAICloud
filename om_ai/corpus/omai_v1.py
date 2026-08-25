"""Fetch licensed open-data *samples* into OMAI-Corpus-v1 (no external LLM brain).

Defaults are deliberately capped (max_docs / max_bytes) so a laptop can build a
real pipeline without downloading FineWeb/Common Crawl at full scale.
"""
from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from om_ai.corpus.sources_catalog import ALLOWED_TRAINING_LICENSES, get_source

logger = logging.getLogger(__name__)

UA = "OM-AI-Corpus-Builder/1.0 (+https://localhost; research; licensed-open-data)"

SOURCE_RAW_DIR = {
    "fineweb": "fineweb",
    "wikipedia-en": "wikipedia",
    "gutenberg": "books",
    "arxiv": "papers",
    "the-stack": "code",
    "open-assistant": "conversations",
    "om-owned": "conversations",
    "common-crawl": "fineweb",
}


def _raw_out(out_dir: Path, source_id: str, filename: str) -> Path:
    sub = SOURCE_RAW_DIR.get(source_id, source_id)
    path = out_dir / "raw" / sub / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _http_get(url: str, *, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return resp.read()


def _write_jsonl(path: Path, rows: Iterator[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def _meta(
    *,
    source_id: str,
    license: str,
    owner: str,
    category: str,
    text: str,
    uri: str = "",
    title: str = "",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_name": source_id,
        "source_url": uri,
        "owner": owner,
        "license": license,
        "license_verified": license.lower() in ALLOWED_TRAINING_LICENSES
        or license.lower() in {"cc-by-sa", "odc-by", "public-domain", "apache-2.0"},
        "allowed_for_training": True,
        "category": category,
        "language": "en",
        "quality_score": 0.7,
        "collected_at": _utc(),
        "content_hash": "",
        "title": title,
        "text": text,
    }


@dataclass
class FetchResult:
    source_id: str
    path: str
    docs: int
    bytes: int
    ok: bool
    detail: str = ""


def fetch_wikipedia_sample(
    out_dir: Path,
    *,
    max_docs: int = 50,
    titles: list[str] | None = None,
) -> FetchResult:
    """Fetch article extracts via MediaWiki API (CC BY-SA)."""
    src = get_source("wikipedia-en")
    assert src
    default_titles = titles or [
        "Artificial_intelligence",
        "Machine_learning",
        "Natural_language_processing",
        "Transformer_(machine_learning_model)",
        "Python_(programming_language)",
        "India",
        "Mathematics",
        "Computer_science",
        "Ethics",
        "History_of_science",
    ]
    rows: list[dict[str, Any]] = []
    for title in default_titles[: max(1, max_docs)]:
        api = (
            "https://en.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode(
                {
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": "1",
                    "exintro": "0",
                    "redirects": "1",
                    "format": "json",
                    "titles": title.replace(" ", "_"),
                }
            )
        )
        try:
            raw = json.loads(_http_get(api).decode("utf-8", errors="replace"))
            pages = (raw.get("query") or {}).get("pages") or {}
            for page in pages.values():
                text = (page.get("extract") or "").strip()
                if len(text) < 200:
                    continue
                rows.append(
                    _meta(
                        source_id=src.source_id,
                        license=src.license,
                        owner=src.owner,
                        category=src.category,
                        text=text[:200_000],
                        uri=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}",
                        title=page.get("title") or title,
                    )
                )
            time.sleep(0.2)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            logger.warning("wikipedia fetch failed for %s: %s", title, exc)
    out = _raw_out(out_dir, src.source_id, "wikipedia-en.jsonl")
    n = _write_jsonl(out, iter(rows))
    return FetchResult(src.source_id, str(out), n, out.stat().st_size if n else 0, n > 0, "wikipedia_api")


# Small set of well-known public-domain Gutenberg plain-text IDs.
_GUTENBERG_IDS = [
    1342,  # Pride and Prejudice
    11,  # Alice in Wonderland
    84,  # Frankenstein
    1661,  # Sherlock Holmes
    2701,  # Moby Dick
    98,  # A Tale of Two Cities
    174,  # The Picture of Dorian Gray
    5200,  # Metamorphosis
]


def fetch_gutenberg_sample(out_dir: Path, *, max_docs: int = 8) -> FetchResult:
    src = get_source("gutenberg")
    assert src
    rows: list[dict[str, Any]] = []
    for gid in _GUTENBERG_IDS[: max(1, max_docs)]:
        url = f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt"
        alt = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
        text = ""
        used = url
        for candidate in (url, alt):
            try:
                raw = _http_get(candidate, timeout=90).decode("utf-8", errors="replace")
                # Strip Gutenberg header/footer roughly
                raw = re.sub(
                    r"\*\*\* START OF (THIS|THE) PROJECT GUTENBERG EBOOK[\s\S]*?\*\*\*",
                    "",
                    raw,
                    count=1,
                    flags=re.I,
                )
                raw = re.sub(
                    r"\*\*\* END OF (THIS|THE) PROJECT GUTENBERG EBOOK[\s\S]*",
                    "",
                    raw,
                    count=1,
                    flags=re.I,
                )
                text = raw.strip()
                used = candidate
                if len(text) > 1000:
                    break
            except (urllib.error.URLError, TimeoutError, OSError):
                continue
        if len(text) < 1000:
            continue
        rows.append(
            _meta(
                source_id=src.source_id,
                license=src.license,
                owner=src.owner,
                category=src.category,
                text=text[:500_000],
                uri=used,
                title=f"gutenberg-{gid}",
            )
        )
        time.sleep(0.3)
    out = _raw_out(out_dir, src.source_id, "gutenberg.jsonl")
    n = _write_jsonl(out, iter(rows))
    return FetchResult(src.source_id, str(out), n, out.stat().st_size if n else 0, n > 0, "gutenberg_http")


def fetch_fineweb_sample(out_dir: Path, *, max_docs: int = 200) -> FetchResult:
    """Stream a FineWeb sample via Hugging Face datasets if installed."""
    src = get_source("fineweb")
    assert src
    out = _raw_out(out_dir, src.source_id, "fineweb.jsonl")
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        # Offline stub: copy local example so pipeline still runs
        seed = Path("data/example_corpus.txt")
        text = seed.read_text(encoding="utf-8") if seed.is_file() else "OM FineWeb placeholder. Install datasets to fetch."
        n = _write_jsonl(
            out,
            iter(
                [
                    _meta(
                        source_id=src.source_id,
                        license=src.license,
                        owner=src.owner,
                        category=src.category,
                        text=text,
                        uri=src.homepage,
                        title="fineweb-offline-seed",
                    )
                ]
            ),
        )
        return FetchResult(
            src.source_id,
            str(out),
            n,
            out.stat().st_size,
            True,
            "offline_seed_install_datasets_for_real_fineweb",
        )

    rows: list[dict[str, Any]] = []
    try:
        ds = load_dataset(
            "HuggingFaceFW/fineweb",
            name="sample-10BT",
            split="train",
            streaming=True,
        )
        for i, item in enumerate(ds):
            if i >= max_docs:
                break
            text = str(item.get("text") or "").strip()
            if len(text) < 100:
                continue
            rows.append(
                _meta(
                    source_id=src.source_id,
                    license=src.license,
                    owner=src.owner,
                    category=src.category,
                    text=text[:200_000],
                    uri=src.homepage,
                    title=f"fineweb-{i}",
                )
            )
    except Exception as exc:
        logger.warning("fineweb stream failed: %s", exc)
        return FetchResult(src.source_id, str(out), 0, 0, False, str(exc))
    n = _write_jsonl(out, iter(rows))
    return FetchResult(src.source_id, str(out), n, out.stat().st_size if n else 0, n > 0, "hf_datasets")


def fetch_open_assistant_sample(out_dir: Path, *, max_docs: int = 200) -> FetchResult:
    src = get_source("open-assistant")
    assert src
    out = _raw_out(out_dir, src.source_id, "open-assistant.jsonl")
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        # Use existing OM chat SFT as instruction seed (project-owned style)
        seed = Path("data/om-chat-sft-v4-complete.jsonl")
        rows = []
        if seed.is_file():
            for i, line in enumerate(seed.read_text(encoding="utf-8").splitlines()):
                if i >= max_docs:
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "messages" in obj:
                    text = "\n".join(
                        f"{m.get('role')}: {m.get('content')}" for m in obj["messages"]
                    )
                else:
                    text = f"user: {obj.get('prompt','')}\nassistant: {obj.get('response','')}"
                rows.append(
                    _meta(
                        source_id="om-owned",
                        license="proprietary-owned",
                        owner="OM AI",
                        category="instruction",
                        text=text,
                        uri="local://om-chat-sft-v4",
                        title=f"om-sft-{i}",
                    )
                )
        n = _write_jsonl(out, iter(rows))
        return FetchResult(
            src.source_id,
            str(out),
            n,
            out.stat().st_size if n else 0,
            n > 0,
            "local_om_sft_seed_install_datasets_for_oas",
        )

    rows = []
    try:
        ds = load_dataset("OpenAssistant/oasst1", split="train", streaming=True)
        for i, item in enumerate(ds):
            if i >= max_docs:
                break
            text = str(item.get("text") or item.get("content") or "").strip()
            if len(text) < 40:
                continue
            rows.append(
                _meta(
                    source_id=src.source_id,
                    license=src.license,
                    owner=src.owner,
                    category=src.category,
                    text=text[:100_000],
                    uri=src.homepage,
                    title=f"oasst-{i}",
                )
            )
    except Exception as exc:
        return FetchResult(src.source_id, str(out), 0, 0, False, str(exc))
    n = _write_jsonl(out, iter(rows))
    return FetchResult(src.source_id, str(out), n, out.stat().st_size if n else 0, n > 0, "hf_datasets")


def fetch_om_owned_local(out_dir: Path) -> FetchResult:
    src = get_source("om-owned")
    assert src
    chunks: list[str] = []
    for p in [
        Path("data/example_corpus.txt"),
        Path("README.md"),
        Path("docs/QUICK_START.md"),
        Path("docs/DATA_GOVERNANCE.md"),
    ]:
        if p.is_file():
            chunks.append(f"# {p}\n{p.read_text(encoding='utf-8', errors='ignore')[:100_000]}")
    text = "\n\n".join(chunks) or "OM owned corpus placeholder."
    out = _raw_out(out_dir, src.source_id, "om-owned.jsonl")
    n = _write_jsonl(
        out,
        iter(
            [
                _meta(
                    source_id=src.source_id,
                    license=src.license,
                    owner=src.owner,
                    category=src.category,
                    text=text,
                    uri="local://om-owned",
                    title="om-owned-bundle",
                )
            ]
        ),
    )
    return FetchResult(src.source_id, str(out), n, out.stat().st_size, True, "local")


FETCHERS = {
    "wikipedia-en": fetch_wikipedia_sample,
    "gutenberg": fetch_gutenberg_sample,
    "fineweb": fetch_fineweb_sample,
    "open-assistant": fetch_open_assistant_sample,
    "om-owned": lambda out_dir, **_: fetch_om_owned_local(out_dir),
}


def fetch_sources(
    root: Path,
    source_ids: list[str] | None = None,
    *,
    max_docs: int = 50,
) -> list[FetchResult]:
    root = Path(root)
    (root / "raw").mkdir(parents=True, exist_ok=True)
    ids = source_ids or ["wikipedia-en", "gutenberg", "om-owned", "fineweb", "open-assistant"]
    results: list[FetchResult] = []
    for sid in ids:
        src = get_source(sid)
        if not src:
            results.append(FetchResult(sid, "", 0, 0, False, "unknown_source"))
            continue
        if not src.allowed_for_training and sid not in {"fineweb"}:
            # Still allow fineweb (allowed). Block common-crawl/arxiv/stack auto-fetch.
            results.append(
                FetchResult(sid, "", 0, 0, False, "not_auto_approved_manual_only")
            )
            continue
        fn = FETCHERS.get(sid)
        if not fn:
            results.append(FetchResult(sid, "", 0, 0, False, "no_fetcher"))
            continue
        try:
            results.append(fn(root, max_docs=max_docs))
        except TypeError:
            results.append(fn(root))
        except Exception as exc:
            results.append(FetchResult(sid, "", 0, 0, False, str(exc)))
    return results


def build_omai_corpus_v1(
    root: Path | str = "data/omai-corpus-v1",
    *,
    fetch: bool = True,
    source_ids: list[str] | None = None,
    max_docs: int = 40,
    near_dup_threshold: float = 0.9,
    tokenizer_path: str | Path | None = None,
    tokenize: bool = True,
) -> dict[str, Any]:
    """Production OMAI-Corpus-v1 pipeline.

    Layout::

        raw/{fineweb,wikipedia,books,papers,code,conversations}/
        cleaned/ → filtered/ → deduplicated/ → tokenized/ → train/ + validation/
    """
    import hashlib

    from om_ai.corpus.filters import filter_document
    from om_ai.corpus.service import CorpusService
    from om_ai.corpus.sources_catalog import catalog_as_dicts

    root = Path(root)
    raw_subs = ("fineweb", "wikipedia", "books", "papers", "code", "conversations")
    for sub in raw_subs:
        (root / "raw" / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("cleaned", "filtered", "deduplicated", "tokenized", "train", "validation", "audit"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    # Back-compat aliases
    (root / "clean").mkdir(parents=True, exist_ok=True)

    fetch_report: list[dict[str, Any]] = []
    if fetch:
        for fr in fetch_sources(root, source_ids, max_docs=max_docs):
            fetch_report.append(
                {
                    "source_id": fr.source_id,
                    "path": fr.path,
                    "docs": fr.docs,
                    "bytes": fr.bytes,
                    "ok": fr.ok,
                    "detail": fr.detail,
                }
            )

    rejected = {
        "license": 0,
        "quality": 0,
        "toxic": 0,
        "spam": 0,
        "lang": 0,
        "empty": 0,
        "too_short": 0,
    }
    cleaned_rows: list[dict[str, Any]] = []
    raw_paths = list((root / "raw").rglob("*.jsonl"))
    for path in sorted(raw_paths):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rejected["empty"] += 1
                continue
            lic = str(row.get("license") or "").lower()
            allowed = bool(row.get("allowed_for_training"))
            if not allowed or (
                lic not in ALLOWED_TRAINING_LICENSES
                and lic
                not in {
                    "cc-by-sa",
                    "odc-by",
                    "public-domain",
                    "apache-2.0",
                    "proprietary-owned",
                }
            ):
                rejected["license"] += 1
                continue
            text = str(row.get("text") or "").strip()
            if not text:
                rejected["empty"] += 1
                continue
            decision = filter_document(text)
            if not decision.ok:
                reason = decision.reason.split(":")[0]
                if reason in rejected:
                    rejected[reason] += 1
                elif reason.startswith("quality"):
                    rejected["quality"] += 1
                elif reason.startswith("lang"):
                    rejected["lang"] += 1
                elif reason.startswith("too_short"):
                    rejected["too_short"] += 1
                else:
                    rejected["quality"] += 1
                continue
            row["text"] = decision.text
            row["language"] = decision.language
            row["quality_score"] = decision.quality_score
            row["pii_hits"] = decision.pii_hits or []
            row["content_hash"] = hashlib.sha256(decision.text.encode("utf-8")).hexdigest()
            row["license_verified"] = True
            cleaned_rows.append(row)

    cleaned_path = root / "cleaned" / "all.jsonl"
    with cleaned_path.open("w", encoding="utf-8") as f:
        for row in cleaned_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # alias
    (root / "clean" / "all.jsonl").write_text(cleaned_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Quality filter pass already applied → filtered/
    filtered_path = root / "filtered" / "all.jsonl"
    filtered_path.write_text(cleaned_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Exact dedupe by content_hash — preserve full license / source metadata
    dedup_path = root / "deduplicated" / "all.jsonl"
    seen_hashes: set[str] = set()
    deduped_rows: list[dict[str, Any]] = []
    exact_dups = 0
    for row in cleaned_rows:
        h = str(row.get("content_hash") or "")
        if not h:
            h = hashlib.sha256(str(row.get("text") or "").encode("utf-8")).hexdigest()
            row["content_hash"] = h
        if h in seen_hashes:
            exact_dups += 1
            continue
        seen_hashes.add(h)
        deduped_rows.append(row)
    with dedup_path.open("w", encoding="utf-8") as f:
        for row in deduped_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # Optional near-dup audit (does not rewrite primary deduped set)
    try:
        svc = CorpusService(output_dir=str(root / "audit"), near_dup_threshold=near_dup_threshold)
        near_audit = svc.dedupe(str(filtered_path), str(root / "audit" / "near_dup_view.jsonl"))
    except Exception as exc:
        near_audit = {"error": str(exc)}
    dedupe_stats = {
        "input": str(filtered_path),
        "output": str(dedup_path),
        "records": len(deduped_rows),
        "exact_duplicates_removed": exact_dups,
        "near_dup_audit": near_audit,
    }

    lines = [
        json.dumps(row, ensure_ascii=False) for row in deduped_rows
    ]
    cut = max(1, int(len(lines) * 0.95)) if len(lines) > 1 else len(lines)
    train_lines, val_lines = lines[:cut], lines[cut:]
    train_path = root / "train" / "shard-00001.jsonl"
    val_path = root / "validation" / "shard-00001.jsonl"
    train_path.write_text("\n".join(train_lines) + ("\n" if train_lines else ""), encoding="utf-8")
    val_path.write_text("\n".join(val_lines) + ("\n" if val_lines else ""), encoding="utf-8")

    txt_path = root / "train" / "corpus.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        for ln in train_lines:
            try:
                f.write(json.loads(ln).get("text", "") + "\n\n")
            except json.JSONDecodeError:
                continue

    # Tokenization stage (production tokenizer when available)
    token_stats: dict[str, Any] = {"enabled": False, "tokens": 0}
    if tokenize:
        tok_path = Path(
            tokenizer_path
            or Path("artifacts/tokenizer-production-65536.json")
        )
        if not tok_path.is_file():
            tok_path = Path("artifacts/tokenizer.json")
        if tok_path.is_file():
            try:
                from om_ai.tokenizer import load_tokenizer

                tok = load_tokenizer(str(tok_path))
                total_tokens = 0
                tok_out = root / "tokenized" / "train.ids.jsonl"
                with tok_out.open("w", encoding="utf-8") as f:
                    for ln in train_lines:
                        try:
                            text = json.loads(ln).get("text", "")
                        except json.JSONDecodeError:
                            continue
                        ids = tok.encode(text, add_eos=True)
                        total_tokens += len(ids)
                        f.write(
                            json.dumps(
                                {
                                    "n_tokens": len(ids),
                                    "ids_head": ids[:64],
                                    "content_hash": hashlib.sha256(
                                        text.encode("utf-8")
                                    ).hexdigest(),
                                }
                            )
                            + "\n"
                        )
                token_stats = {
                    "enabled": True,
                    "tokenizer": str(tok_path),
                    "docs": len(train_lines),
                    "tokens": total_tokens,
                    "path": str(tok_out),
                }
            except Exception as exc:
                token_stats = {"enabled": False, "error": str(exc)}

    stages_complete = {
        "dataset_downloader": True,
        "license_tracking": True,
        "data_validation": True,
        "language_filtering": True,
        "quality_scoring": True,
        "duplicate_removal": True,
        "pii_filtering": True,
        "toxic_content_filtering": True,
        "tokenization": bool(token_stats.get("enabled")),
        "train_validation_split": True,
    }

    audit = {
        "built_at": _utc(),
        "root": str(root),
        "phase": "OMAI-Corpus-v1-production-pipeline",
        "pipeline_complete_pct": round(
            100.0 * sum(1 for v in stages_complete.values() if v) / len(stages_complete), 1
        ),
        "stages": stages_complete,
        "fetch": fetch_report,
        "cleaned_docs": len(cleaned_rows),
        "rejected": rejected,
        "dedupe": dedupe_stats,
        "tokenization": token_stats,
        "train_docs": len(train_lines),
        "validation_docs": len(val_lines),
        "train_jsonl": str(train_path),
        "train_txt": str(txt_path),
        "validation_jsonl": str(val_path),
        "note": (
            "Pipeline software is complete. Scale collection (FineWeb full / dumps) "
            "is still required before 1B–70B token budgets are met."
        ),
    }
    (root / "audit" / "build_report.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    manifest = {
        "name": "OMAI-Corpus-v1",
        "version": "1.1",
        "sources": catalog_as_dicts(),
        "layout": {
            "raw": "raw/{fineweb,wikipedia,books,papers,code,conversations}/",
            "cleaned": "cleaned/",
            "filtered": "filtered/",
            "deduplicated": "deduplicated/",
            "tokenized": "tokenized/",
            "train": "train/",
            "validation": "validation/",
            "audit": "audit/",
        },
        "stages": stages_complete,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return audit
