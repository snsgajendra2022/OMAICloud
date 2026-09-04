from dataclasses import dataclass
from typing import Any


@dataclass
class VisionInput:

    image_path: str

    metadata: dict | None = None



@dataclass
class VisionResult:

    description: str

    objects: list[str]

    extracted_text: str

    confidence: float

    metadata: dict[str, Any]