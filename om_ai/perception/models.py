from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PerceptionInput:

    input_type: str

    content: Any

    metadata: Optional[dict] = None


@dataclass
class PerceptionResult:

    input_type: str

    understanding: str

    extracted_data: dict

    confidence: float