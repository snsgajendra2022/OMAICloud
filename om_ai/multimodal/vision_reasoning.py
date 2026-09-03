"""Answer vision questions from image analysis packets."""
from __future__ import annotations

from typing import Any


class VisionReasoning:
    def answer(self, question: str, analysis: dict[str, Any]) -> str:
        q = (question or "").strip().lower()
        summary = str(analysis.get("summary") or "").strip()
        ui = analysis.get("ui") or {}
        ocr = analysis.get("ocr") or {}
        objects = analysis.get("objects") or []

        if any(x in q for x in ("what is wrong", "issue", "bug", "error")):
            return (
                "Based on the visual cues, review:\n"
                "- Layout alignment / spacing\n"
                "- Contrast and readability of text\n"
                "- Missing labels or truncated content\n"
                f"- Detected regions: {', '.join(objects)}\n"
                + (f"\nOCR hints:\n{(ocr.get('text') or '')[:600]}\n" if ocr.get("text") else "")
            )

        if any(x in q for x in ("improve", "redesign", "better")):
            return (
                "Improvement ideas:\n"
                "1. Strengthen visual hierarchy (title → actions → content)\n"
                "2. Group related cards; reduce clutter\n"
                "3. Ensure accessible contrast\n"
                "4. Make primary CTA obvious\n"
                + (f"\nCurrent components: {', '.join(ui.get('components') or objects)}\n")
            )

        if any(x in q for x in ("create similar", "recreate", "clone design", "similar design")):
            tech = ", ".join(ui.get("possible_technology") or ["React", "Tailwind"])
            return (
                "Similar design brief:\n"
                f"- Stack suggestion: {tech}\n"
                f"- Components: {', '.join(ui.get('components') or objects)}\n"
                "- Use a 12-column grid, sticky sidebar, metric cards, chart panel\n"
                "- Provide dark/light tokens and spacing scale\n"
            )

        if any(x in q for x in ("extract", "fields", "invoice", "data")):
            fields = ocr.get("fields") or {}
            if fields:
                lines = "\n".join(f"- {k}: {v}" for k, v in fields.items())
                return f"Extracted fields:\n{lines}\n"
            if ocr.get("text"):
                return f"Extracted text:\n{ocr['text'][:1500]}\n"
            return "No reliable text fields extracted yet. Try a sharper image or install OCR (pytesseract).\n"

        if any(x in q for x in ("explain", "diagram", "what is in", "describe", "see")) or not q:
            return summary or "Image analyzed; no strong description available.\n"

        return summary or f"Vision analysis complete. Objects: {', '.join(objects)}.\n"
