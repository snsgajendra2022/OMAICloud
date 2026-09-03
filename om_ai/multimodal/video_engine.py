"""Video understanding stub with metadata."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class VideoEngine:
    def analyze(self, source: str | Path | bytes, *, question: str = "") -> dict[str, Any]:
        path = Path(source) if isinstance(source, (str, Path)) else None
        exists = bool(path and path.is_file())
        size = path.stat().st_size if exists else (len(source) if isinstance(source, (bytes, bytearray)) else 0)
        return {
            "ok": exists or size > 0,
            "type": "video",
            "bytes": size,
            "frames_analyzed": 0,
            "engine": "pending_ffmpeg",
            "summary": (
                "Video received. Frame sampling / captioning requires ffmpeg + vision stack."
                if exists or size
                else "No video payload."
            ),
            "question": question,
        }
