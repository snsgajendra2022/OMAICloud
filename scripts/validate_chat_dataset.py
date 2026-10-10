#!/usr/bin/env python3
"""Validate chat/SFT datasets and emit a reproducible manifest without printing records.

Accepted JSONL records:
  {"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
  {"prompt":"...", "completion":"..."}
Parquet support is optional and requires pandas + a Parquet engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


_ALLOWED_ROLES = {"system", "developer", "user", "assistant", "tool"}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def record_text(record: Any, line_no: int) -> str:
    if not isinstance(record, dict):
        raise ValueError(f"record {line_no}: expected JSON object")
    if isinstance(record.get("messages"), list):
        messages = record["messages"]
        if not messages:
            raise ValueError(f"record {line_no}: messages must not be empty")
        normalized = []
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValueError(f"record {line_no}: messages[{index}] must be an object")
            role = message.get("role")
            content = message.get("content")
            if role not in _ALLOWED_ROLES:
                raise ValueError(f"record {line_no}: unsupported role at messages[{index}]")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"record {line_no}: empty/non-string content at messages[{index}]")
            normalized.append(f"{role}: {normalize(content)}")
        if not any(m.startswith("assistant:") for m in normalized):
            raise ValueError(f"record {line_no}: conversation has no assistant target")
        return "\n".join(normalized)
    prompt, completion = record.get("prompt"), record.get("completion")
    if isinstance(prompt, str) and prompt.strip() and isinstance(completion, str) and completion.strip():
        return f"user: {normalize(prompt)}\nassistant: {normalize(completion)}"
    raise ValueError(f"record {line_no}: expected messages or non-empty prompt/completion")


def read_records(path: Path) -> list[Any]:
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_no}: invalid JSON: {exc.msg}") from exc
        return records
    if suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("JSON dataset root must be an array")
        return value
    if suffix == ".parquet":
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Parquet support requires pandas and pyarrow or fastparquet") from exc
        return pd.read_parquet(path).to_dict(orient="records")
    if suffix in {".txt", ".text"}:
        return [{"prompt": "Continue the text.", "completion": line.strip()} for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    raise ValueError(f"Unsupported dataset extension: {suffix}")


def validate(path: Path, eval_path: Path | None = None) -> dict[str, Any]:
    raw_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    records = read_records(path)
    fingerprints: Counter[str] = Counter()
    errors: list[str] = []
    lengths: list[int] = []
    valid = 0
    for index, record in enumerate(records, 1):
        try:
            text = record_text(record, index)
            fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
            fingerprints[fingerprint] += 1
            lengths.append(len(text))
            valid += 1
        except ValueError as exc:
            errors.append(str(exc))
    eval_hashes: set[str] = set()
    if eval_path:
        for index, record in enumerate(read_records(eval_path), 1):
            try:
                eval_text = record_text(record, index)
                eval_hashes.add(hashlib.sha256(eval_text.encode("utf-8")).hexdigest())
            except ValueError:
                continue
    train_hashes = set(fingerprints)
    duplicates = sum(count - 1 for count in fingerprints.values() if count > 1)
    contamination = len(train_hashes & eval_hashes)
    return {
        "schema_version": 1,
        "source": str(path),
        "source_sha256": raw_sha,
        "format": path.suffix.lower().lstrip("."),
        "records_total": len(records),
        "records_valid": valid,
        "records_invalid": len(errors),
        "exact_duplicate_records": duplicates,
        "unique_valid_records": len(fingerprints),
        "eval_source": str(eval_path) if eval_path else None,
        "eval_exact_overlap_unique_records": contamination,
        "character_length": {
            "min": min(lengths) if lengths else None,
            "max": max(lengths) if lengths else None,
            "mean": round(sum(lengths) / len(lengths), 2) if lengths else None,
        },
        "errors": errors[:100],
        "ok": not errors and len(records) > 0 and contamination == 0,
        "notes": [
            "Exact duplicate and exact evaluation-overlap checks only; semantic near-duplicate and contamination checks require a separate reviewed pipeline.",
            "This tool validates schema and provenance hashes; it does not establish dataset licensing or training quality.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--eval-dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate(args.dataset, args.eval_dataset)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"errors"}}, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
