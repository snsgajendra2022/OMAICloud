from __future__ import annotations
from typing import Any
from .camera_manager import CameraManager
from .image_analyzer import ImageAnalyzer
from .screen_reader import ScreenReader
from .visual_memory import VisualMemory

class VisionEngine:
    def __init__(self) -> None:
        self.camera = CameraManager()
        self.screen = ScreenReader()
        self.analyzer = ImageAnalyzer()
        self.memory = VisualMemory()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 107, "name": "Vision Intelligence"}

    def what_is_wrong(self) -> dict[str, Any]:
        screen = self.screen.read() if hasattr(self.screen, "read") else {}
        analysis = self.analyzer.analyze(screen if isinstance(screen, dict) else {})
        return {"screen": screen, "analysis": analysis}
