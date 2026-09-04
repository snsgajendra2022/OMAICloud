from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentInput:

    path: str

    document_type: str

    metadata: dict | None = None



@dataclass
class DocumentResult:

    document_type: str

    title: str

    content: str

    sections: list[str]

    extracted_data: dict[str, Any]

    confidence: float