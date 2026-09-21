"""Image understanding facade."""
from __future__ import annotations

from typing import Any

from .vision_engine import VisionEngine


class ImageUnderstanding:
    def __init__(self) -> None:
        self.vision = VisionEngine()

    def run(self, image_ref: str | bytes | None, *, prompt: str = "") -> dict[str, Any]:
        pack = self.vision.understand(image_ref, hint=prompt)
        pack["prompt"] = prompt
        return pack
