from __future__ import annotations
from abc import ABC, abstractmethod

class VisionBackend(ABC):
    @abstractmethod
    def describe_image(self, image_path:str) -> dict: ...

class NullVisionBackend(VisionBackend):
    def describe_image(self,image_path:str)->dict:
        return {'available':False,'message':'Attach a local vision model backend (e.g. your own trained encoder/VLM) to enable image understanding.','image_path':image_path}
