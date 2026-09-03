"""
Multimodal Intelligence Manager

Any Input → route → modality engines → vision reasoning → structured packet
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .input_router import InputRouter
from .image_engine import ImageEngine
from .document_engine import DocumentEngine
from .audio_engine import AudioEngine
from .video_engine import VideoEngine
from .vision_reasoning import VisionReasoning
from .ocr_engine import OCREngine


class MultimodalManager:
    def __init__(self) -> None:
        self.router = InputRouter()
        self.image = ImageEngine()
        self.document = DocumentEngine()
        self.audio = AudioEngine()
        self.video = VideoEngine()
        self.vision = VisionReasoning()
        self.ocr = OCREngine()

    def process(
        self,
        *,
        text: str = "",
        path: str | Path | None = None,
        mime: str | None = None,
        raw: bytes | None = None,
        question: str = "",
    ) -> dict[str, Any]:
        q = (question or text or "").strip()
        route = self.router.classify(text=text, path=path, mime=mime, raw=raw)
        primary = route["primary"]
        stages = ["received", "routed"]
        analysis: dict[str, Any] = {}
        answer = ""

        if primary == "image":
            stages += ["validate_image", "ocr", "objects", "vision_reason"]
            analysis = self.image.analyze(path or raw or b"", question=q)
            answer = self.vision.answer(q, analysis)
        elif primary == "document" or primary == "code":
            stages += ["parse_document"]
            analysis = self.document.analyze(path or raw or b"", question=q)
            answer = self._doc_answer(q, analysis)
        elif primary == "audio":
            stages += ["audio"]
            analysis = self.audio.analyze(path or raw or b"", question=q)
            answer = analysis.get("summary") or ""
        elif primary == "video":
            stages += ["video"]
            analysis = self.video.analyze(path or raw or b"", question=q)
            answer = analysis.get("summary") or ""
        else:
            stages += ["text_passthrough"]
            analysis = {"type": "text", "text": text}
            answer = ""

        return {
            "route": route,
            "stages": stages,
            "analysis": analysis,
            "answer": (answer or "").rstrip() + ("\n" if answer else ""),
            "ocr": analysis.get("ocr") if isinstance(analysis, dict) else None,
            "modality": primary,
            "ok": True,
        }

    def _doc_answer(self, question: str, analysis: dict[str, Any]) -> str:
        summary = (analysis.get("summary") or "").strip()
        if not summary:
            return "Document received but no text could be extracted.\n"
        if question:
            return f"**Document insight for:** {question}\n\n{summary[:2000]}\n"
        return f"**Document extract:**\n\n{summary[:2000]}\n"
