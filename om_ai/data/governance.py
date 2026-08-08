from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json
from typing import Iterable


@dataclass(slots=True)
class SourceManifest:
    source_id: str
    uri: str
    license: str
    owner: str
    allowed_for_training: bool
    category: str = "general"
    language: str = "und"
    version: str = "1"
    notes: str = ""

    def validate(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if not self.license.strip() or self.license.lower() == "unknown":
            raise ValueError(f"source {self.source_id!r} must declare a license")
        if not self.owner.strip():
            raise ValueError(f"source {self.source_id!r} must declare an owner")
        if not self.allowed_for_training:
            raise PermissionError(f"source {self.source_id!r} is not approved for model training")


class CorpusGovernance:
    """License-first corpus manifest and immutable audit helpers."""

    @staticmethod
    def load_manifest(path: str | Path) -> list[SourceManifest]:
        raw = json.loads(Path(path).read_text())
        rows = raw if isinstance(raw, list) else raw.get("sources", [])
        manifests = [SourceManifest(**row) for row in rows]
        for item in manifests:
            item.validate()
        return manifests

    @staticmethod
    def save_manifest(items: Iterable[SourceManifest], path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"sources": [asdict(x) for x in items]}, indent=2, ensure_ascii=False))

    @staticmethod
    def sha256_file(path: str | Path) -> str:
        h = sha256()
        with Path(path).open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def write_audit(records: list[dict], path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(records, indent=2, ensure_ascii=False))
