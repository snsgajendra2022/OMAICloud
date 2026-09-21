"""Route voice / vision / screen into one multimodal pack."""
from __future__ import annotations

import re
from typing import Any

from .document_vision import DocumentVision
from .environment_context import EnvironmentContext
from .image_understanding import ImageUnderstanding
from .screen_analyzer import ScreenAnalyzer
from .vision_engine import VisionEngine

_ROUTER: "MultimodalRouter | None" = None


class MultimodalRouter:
    def __init__(self) -> None:
        self.vision = VisionEngine()
        self.screen = ScreenAnalyzer()
        self.images = ImageUnderstanding()
        self.docs = DocumentVision()
        self.env = EnvironmentContext()

    def route(
        self,
        message: str,
        *,
        image_ref: str | bytes | None = None,
        screen_ref: str | None = None,
        doc_ref: str | None = None,
        project: str = "",
    ) -> dict[str, Any]:
        low = (message or "").lower()
        wants_vision = bool(image_ref or screen_ref) or bool(
            re.search(r"(?i)\b(what is wrong here|look at|see this|on (my )?screen|this error)\b", low)
        )
        env = self.env.update(project=project, screen=screen_ref or "")
        pack: dict[str, Any] = {
            "multimodal": wants_vision or bool(doc_ref),
            "environment": env,
            "system_hint": "",
        }
        if screen_ref or wants_vision:
            scr = self.screen.analyze(screen_ref, user_question=message)
            vis = self.vision.understand(image_ref or screen_ref, hint=message)
            pack["screen"] = scr
            pack["vision"] = vis
            pack["system_hint"] = " ".join(
                p for p in (scr.get("system_hint"), vis.get("summary")) if p
            )
        if image_ref and not screen_ref:
            pack["image"] = self.images.run(image_ref, prompt=message)
        if doc_ref:
            pack["document"] = self.docs.read(doc_ref)
            pack["system_hint"] = (pack.get("system_hint") or "") + " " + pack["document"].get(
                "system_hint", ""
            )
        return pack


def get_multimodal_router() -> MultimodalRouter:
    global _ROUTER
    if _ROUTER is None:
        _ROUTER = MultimodalRouter()
    return _ROUTER
