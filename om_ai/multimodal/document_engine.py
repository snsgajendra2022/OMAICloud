"""Document understanding (PDF/text/code files)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class DocumentEngine:
    def analyze(self, source: str | Path | bytes, *, question: str = "") -> dict[str, Any]:
        path = Path(source) if isinstance(source, (str, Path)) else None
        text = ""
        kind = "document"
        if path and path.is_file():
            kind = path.suffix.lower().lstrip(".") or "document"
            try:
                if path.suffix.lower() in {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".tsx", ".html", ".css", ".sql"}:
                    text = path.read_text(encoding="utf-8", errors="ignore")[:50_000]
                elif path.suffix.lower() == ".pdf":
                    text = self._pdf_text(path)
                else:
                    text = path.read_text(encoding="utf-8", errors="ignore")[:20_000]
            except Exception as exc:
                return {"ok": False, "error": str(exc), "type": kind, "text": "", "summary": ""}
        elif isinstance(source, (bytes, bytearray)):
            text = bytes(source).decode("utf-8", errors="ignore")[:50_000]

        summary = text.strip()[:1500]
        return {
            "ok": True,
            "type": kind,
            "text": text,
            "chars": len(text),
            "summary": summary,
            "question": question,
        }

    def _pdf_text(self, path: Path) -> str:
        try:
            # Optional dependency
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            parts = []
            for page in reader.pages[:20]:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)
        except Exception:
            return ""
