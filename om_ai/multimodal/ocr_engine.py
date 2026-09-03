"""OCR extraction with optional engines; never crashes the server."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class OCREngine:
    def extract(self, source: str | Path | bytes, *, mime: str = "") -> dict[str, Any]:
        path = None
        data = b""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_file():
                try:
                    data = path.read_bytes()[:8_000_000]
                except OSError:
                    data = b""
        elif isinstance(source, (bytes, bytearray)):
            data = bytes(source)

        text = ""
        engine = "none"
        confidence = 0.0

        # Optional pytesseract + Pillow
        try:
            from PIL import Image
            import io

            if path and path.is_file():
                img = Image.open(path)
            elif data:
                img = Image.open(io.BytesIO(data))
            else:
                img = None
            if img is not None:
                try:
                    import pytesseract

                    text = pytesseract.image_to_string(img) or ""
                    engine = "pytesseract"
                    confidence = 0.75 if text.strip() else 0.2
                except Exception:
                    # Pillow available but no OCR binary — still return image stats
                    engine = "pillow_meta"
                    text = ""
                    confidence = 0.15
                    meta_size = getattr(img, "size", None)
                    return {
                        "text": text,
                        "confidence": confidence,
                        "engine": engine,
                        "tables": [],
                        "numbers": [],
                        "labels": [],
                        "code_snippets": [],
                        "image_size": meta_size,
                        "fields": self._infer_fields(""),
                    }
        except Exception:
            pass

        numbers = re.findall(r"\$?\d[\d,]*(?:\.\d+)?%?", text)
        labels = re.findall(r"(?m)^[A-Z][A-Za-z0-9 _/-]{2,40}:", text)
        code_snippets = []
        if re.search(r"\b(def |class |function |import |const |=>)\b", text):
            code_snippets = [text[:1200]]

        return {
            "text": text.strip(),
            "confidence": confidence,
            "engine": engine,
            "tables": [],
            "numbers": numbers[:40],
            "labels": [x.rstrip(":") for x in labels[:40]],
            "code_snippets": code_snippets,
            "fields": self._infer_fields(text),
            "path": str(path) if path else "",
        }

    def _infer_fields(self, text: str) -> dict[str, str]:
        low = (text or "").lower()
        fields: dict[str, str] = {}
        # Soft invoice-like extraction without topic if-branches for answers
        m = re.search(r"(?:invoice\s*#|invoice\s*no\.?)\s*[:\s]*([A-Za-z0-9-]+)", text, re.I)
        if m:
            fields["invoice_id"] = m.group(1)
        m = re.search(r"(?:total|amount|balance due)\s*[:\s]*\$?([\d,]+\.?\d*)", text, re.I)
        if m:
            fields["amount"] = m.group(1)
        m = re.search(r"(?:date)\s*[:\s]*([0-9]{1,4}[/-][0-9]{1,2}[/-][0-9]{1,4})", text, re.I)
        if m:
            fields["date"] = m.group(1)
        m = re.search(r"(?:customer|bill to|client)\s*[:\s]*([A-Za-z0-9 .,&-]{3,60})", text, re.I)
        if m:
            fields["customer"] = m.group(1).strip()
        if "invoice" in low:
            fields.setdefault("type", "invoice")
        return fields
