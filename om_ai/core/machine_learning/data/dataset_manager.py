"""Validated, deterministic, content-addressed JSONL learning datasets."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable


class DatasetValidationError(ValueError):
    """Raised when a training example is incomplete or unsafe to use."""


class DatasetManager:
    REQUIRED_FIELDS = ("question", "answer")

    def __init__(self, root: str | Path = "artifacts/learning/datasets") -> None:
        self.root = Path(root)

    @staticmethod
    def normalize(record: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise DatasetValidationError("Each dataset example must be an object.")
        normalized = {str(k).strip(): v for k, v in record.items() if str(k).strip()}
        for field in DatasetManager.REQUIRED_FIELDS:
            value = normalized.get(field)
            if not isinstance(value, str) or not value.strip():
                raise DatasetValidationError(f"Missing required non-empty field: {field}")
            normalized[field] = value.strip()
        normalized["question"] = normalized["question"][:12000]
        normalized["answer"] = normalized["answer"][:24000]
        for field in ("intent", "domain", "meaning", "goal", "reasoning_strategy",
                      "verification_strategy", "source", "conversation_id"):
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = normalized[field].strip()[:2000]
        if "quality_score" in normalized:
            try:
                score = float(normalized["quality_score"])
            except (TypeError, ValueError) as exc:
                raise DatasetValidationError("quality_score must be numeric.") from exc
            if not 0.0 <= score <= 1.0:
                raise DatasetValidationError("quality_score must be between 0 and 1.")
            normalized["quality_score"] = score
        return normalized

    def create_version(self, records: Iterable[dict[str, Any]]) -> dict[str, Any]:
        clean: list[dict[str, Any]] = []
        for record in records:
            try:
                clean.append(self.normalize(record))
            except DatasetValidationError:
                raise
        if not clean:
            raise DatasetValidationError("Cannot create an empty dataset version.")
        lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in clean]
        payload = ("\n".join(lines) + "\n").encode("utf-8")
        version = hashlib.sha256(payload).hexdigest()[:16]
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.root / f"{version}.jsonl"
        if not destination.exists():
            self._atomic_write(destination, payload)
        manifest = {
            "dataset_version": version,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "count": len(clean),
            "schema_version": 1,
            "path": str(destination),
        }
        manifest_path = self.root / f"{version}.manifest.json"
        self._atomic_write(
            manifest_path,
            (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )
        return manifest

    def load(self, version: str) -> list[dict[str, Any]]:
        if not version or any(char not in "0123456789abcdef" for char in version.lower()):
            raise ValueError("Invalid dataset version.")
        path = self.root / f"{version}.jsonl"
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DatasetValidationError(f"Invalid JSON on line {line_number}.") from exc
                rows.append(self.normalize(row))
        return rows

    @staticmethod
    def split(
        records: list[dict[str, Any]],
        train_ratio: float = 0.8,
        validation_ratio: float = 0.1,
        test_ratio: float = 0.1,
    ) -> dict[str, list[dict[str, Any]]]:
        ratios = (train_ratio, validation_ratio, test_ratio)
        if any(r < 0 or r > 1 for r in ratios) or abs(sum(ratios) - 1.0) > 1e-8:
            raise ValueError("Split ratios must be in [0, 1] and sum to 1.")
        ordered = sorted(records, key=lambda row: hashlib.sha256(
            json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest())
        n = len(ordered)
        train_end = int(n * train_ratio)
        validation_end = train_end + int(n * validation_ratio)
        # Give rounding remainder to test to keep every row accounted for.
        return {
            "train": ordered[:train_end],
            "validation": ordered[train_end:validation_end],
            "test": ordered[validation_end:],
        }

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
