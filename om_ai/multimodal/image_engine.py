"""Image validation + visual structure understanding."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .ocr_engine import OCREngine


class ImageEngine:
    def __init__(self) -> None:
        self.ocr = OCREngine()

    def analyze(self, source: str | Path | bytes, *, question: str = "") -> dict[str, Any]:
        path = Path(source) if isinstance(source, (str, Path)) else None
        valid = True
        reason = "ok"
        width = height = None
        fmt = None

        try:
            from PIL import Image
            import io

            if path and path.is_file():
                img = Image.open(path)
            elif isinstance(source, (bytes, bytearray)):
                img = Image.open(io.BytesIO(bytes(source)))
            else:
                img = None
                valid = False
                reason = "unreadable"
            if img is not None:
                width, height = img.size
                fmt = img.format
                if width * height > 40_000_000:
                    valid = False
                    reason = "image too large"
        except Exception as exc:
            valid = path is not None and path.is_file()
            reason = f"pillow unavailable or decode issue: {exc}" if not valid else "file present"

        ocr = self.ocr.extract(source)
        objects = self._heuristic_objects(ocr, width, height, question)
        ui = self._ui_guess(ocr, objects, question)

        return {
            "valid": valid,
            "reason": reason,
            "format": fmt,
            "width": width,
            "height": height,
            "ocr": ocr,
            "objects": objects,
            "ui": ui,
            "type": ocr.get("fields", {}).get("type") or ui.get("type") or "image",
            "summary": self._summary(ui, ocr, objects),
        }

    def _heuristic_objects(self, ocr: dict, width, height, question: str) -> list[str]:
        objs: list[str] = []
        text = (ocr.get("text") or "").lower()
        q = (question or "").lower()
        blob = text + " " + q
        catalog = [
            ("sidebar", ("sidebar", "menu", "navigation")),
            ("cards", ("card", "widget", "tile")),
            ("charts", ("chart", "graph", "analytics")),
            ("navigation", ("nav", "navbar", "header")),
            ("table", ("table", "rows", "columns")),
            ("form", ("input", "login", "password", "submit")),
            ("button", ("button", "cta")),
        ]
        for name, cues in catalog:
            if any(c in blob for c in cues):
                objs.append(name)
        if width and height and width > height * 1.2:
            objs.append("landscape_frame")
        return objs or ["visual_content"]

    def _ui_guess(self, ocr: dict, objects: list[str], question: str) -> dict[str, Any]:
        comps = [o for o in objects if o in {"sidebar", "cards", "charts", "navigation", "table", "form", "button"}]
        is_ui = len(comps) >= 2 or "dashboard" in (question or "").lower() or "ui" in (question or "").lower()
        tech = []
        if is_ui:
            tech = ["React", "Tailwind"]  # likely stack suggestion, not a hard claim of detection
        return {
            "type": "dashboard_ui" if is_ui else "general_image",
            "components": comps,
            "possible_technology": tech,
        }

    def _summary(self, ui: dict, ocr: dict, objects: list[str]) -> str:
        if ui.get("type") == "dashboard_ui":
            comps = ", ".join(ui.get("components") or objects)
            tech = ", ".join(ui.get("possible_technology") or [])
            return (
                f"This looks like a dashboard UI.\n\n"
                f"Components:\n- " + "\n- ".join((ui.get("components") or objects)[:8]) + "\n\n"
                + (f"Technology possible:\n- {tech.replace(', ', chr(10)+'- ')}\n" if tech else "")
            )
        text = (ocr.get("text") or "").strip()
        if text:
            return f"Image text extracted ({ocr.get('engine')}):\n{text[:1200]}\n"
        return f"Image received. Detected cues: {', '.join(objects)}.\n"
