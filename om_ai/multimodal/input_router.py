"""Route any input blob to the right modality engine — by content signals, not topic keywords."""
from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any


IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
DOC_EXT = {".pdf", ".txt", ".md", ".docx", ".csv", ".json", ".html"}
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".css", ".html", ".sql"}


class InputRouter:
    def classify(
        self,
        *,
        text: str | None = None,
        path: str | Path | None = None,
        mime: str | None = None,
        raw: bytes | None = None,
    ) -> dict[str, Any]:
        modalities: list[str] = []
        meta: dict[str, Any] = {"mime": mime or "", "path": str(path or "")}

        if text and str(text).strip():
            modalities.append("text")

        p = Path(path) if path else None
        ext = (p.suffix.lower() if p else "")
        guessed, _ = mimetypes.guess_type(str(p) if p else "")
        mime = (mime or guessed or "").lower()

        if ext in IMAGE_EXT or mime.startswith("image/"):
            modalities.append("image")
        elif ext in DOC_EXT or mime in {"application/pdf", "text/plain", "text/markdown"}:
            modalities.append("document")
        elif ext in AUDIO_EXT or mime.startswith("audio/"):
            modalities.append("audio")
        elif ext in VIDEO_EXT or mime.startswith("video/"):
            modalities.append("video")
        elif ext in CODE_EXT:
            modalities.append("code")
            modalities.append("document")

        # Magic-byte sniff for images when extension missing
        if raw and "image" not in modalities:
            if raw[:8] == b"\x89PNG\r\n\x1a\n" or raw[:3] == b"\xff\xd8\xff" or raw[:4] == b"RIFF":
                modalities.append("image")

        if not modalities:
            modalities = ["text"] if text else ["unknown"]

        primary = modalities[0]
        # Prefer richer modality when text + file
        if "image" in modalities:
            primary = "image"
        elif "video" in modalities:
            primary = "video"
        elif "audio" in modalities:
            primary = "audio"
        elif "document" in modalities or "code" in modalities:
            primary = "document" if "document" in modalities else "code"

        return {
            "primary": primary,
            "modalities": modalities,
            "extension": ext,
            "meta": meta,
        }
