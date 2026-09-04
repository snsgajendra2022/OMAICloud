from dataclasses import dataclass
from typing import Any


@dataclass
class PDFDocument:

    file_path: str

    pages: int

    title: str

    author: str

    text: str

    tables: list[Any]

    images: list[Any]

    metadata: dict