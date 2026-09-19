from __future__ import annotations
from typing import Any
from .camera_manager import CameraManager
from .image_understanding import ImageUnderstanding
from .screen_reader import ScreenReader
from .visual_memory import VisualMemory

_RT = None

class VisionRuntime:
    def __init__(self) -> None:
        self.camera = CameraManager()
        self.images = ImageUnderstanding()
        self.screen = ScreenReader()
        self.memory = VisualMemory()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 58,
            "name": "Vision Intelligence",
            "camera": self.camera.status(),
            "screen": {"permissioned": False},
        }

    def what_is_on_screen(self) -> dict[str, Any]:
        snap = self.screen.snapshot()
        desc = self.images.describe(snap)
        if desc.get("summary"):
            self.memory.add(str(desc["summary"]))
        return {"screen": snap, "understanding": desc}


def get_vision_runtime() -> VisionRuntime:
    global _RT
    if _RT is None:
        _RT = VisionRuntime()
    return _RT
