"""Audio understanding stub with real file validation."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AudioEngine:
    def analyze(self, source: str | Path | bytes, *, question: str = "") -> dict[str, Any]:
        path = Path(source) if isinstance(source, (str, Path)) else None
        exists = bool(path and path.is_file())
        size = path.stat().st_size if exists else (len(source) if isinstance(source, (bytes, bytearray)) else 0)
        return {
            "ok": exists or isinstance(source, (bytes, bytearray)),
            "type": "audio",
            "bytes": size,
            "transcript": "",
            "engine": "pending_whisper",
            "summary": (
                "Audio received. Speech-to-text engine is not configured; "
                "install whisper/voice extras to enable transcripts."
                if exists or size
                else "No audio payload."
            ),
            "question": question,
        }
