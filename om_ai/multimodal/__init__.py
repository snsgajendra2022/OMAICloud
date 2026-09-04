"""
STEP 89 — OM Multimodal Intelligence Fusion

Combine text + image + PDF (+ audio/video stubs) into one understanding pack.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class MultimodalFusion:
    def fuse(
        self,
        *,
        question: str = "",
        image_path: str | None = None,
        pdf_path: str | None = None,
        audio_path: str | None = None,
        video_path: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        parts: list[str] = []
        modalities: list[str] = []
        details: dict[str, Any] = {}

        if question:
            modalities.append("text")
            parts.append(f"[text] {question.strip()}")

        if image_path and Path(image_path).is_file():
            modalities.append("image")
            try:
                from om_ai.perception.vision.vision_engine import VisionEngine

                vis = VisionEngine().analyze(image_path)  # type: ignore[attr-defined]
                details["image"] = vis
                parts.append(f"[image] {vis}"[:1500])
            except Exception:
                try:
                    from om_ai.operating_intelligence import perception_bridge

                    fn = getattr(perception_bridge, "analyze_image", None)
                    if callable(fn):
                        vis = fn(image_path, question=question)
                        details["image"] = vis
                        parts.append(f"[image] {vis}"[:1500])
                    else:
                        parts.append(f"[image] path={image_path}")
                except Exception as exc:
                    parts.append(f"[image] unavailable: {exc}")

        if pdf_path and Path(pdf_path).is_file():
            modalities.append("pdf")
            try:
                from om_ai.perception.document.pdf.pdf_engine import PDFEngine

                pdf = PDFEngine().process(pdf_path)  # type: ignore[attr-defined]
                details["pdf"] = pdf
                parts.append(f"[pdf] {pdf}"[:2000])
            except Exception:
                try:
                    from om_ai.perception.document.pdf_reader import read_pdf

                    text = read_pdf(pdf_path)
                    details["pdf"] = {"text_len": len(text or "")}
                    parts.append(f"[pdf] {(text or '')[:2000]}")
                except Exception as exc:
                    parts.append(f"[pdf] unavailable: {exc}")

        if audio_path:
            modalities.append("audio")
            parts.append(f"[audio] pending STT: {audio_path}")
            details["audio"] = {"path": audio_path, "status": "stt_pending"}

        if video_path:
            modalities.append("video")
            parts.append(f"[video] pending analysis: {video_path}")
            details["video"] = {"path": video_path, "status": "pending"}

        if extra:
            details["extra"] = extra

        fused = "\n\n".join(parts).strip()
        return {
            "modalities": modalities,
            "fused_text": fused,
            "details": details,
            "ok": bool(fused),
            "question": question,
        }
