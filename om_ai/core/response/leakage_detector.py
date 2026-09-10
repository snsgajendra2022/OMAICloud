"""Dataset / training-leakage protection for public answers."""
from __future__ import annotations

import re


class LeakageDetector:

    BLOCKED = [
        "Question:",
        "Answer:",
        ".jsonl",
        "training example",
        "dataset",
        "domain:",
    ]

    # "Source:" alone is too aggressive (blocks legitimate Sources: citations).
    # Only flag dataset-style "Source: ..." rows when paired with Q/A markers.
    _DATASET_ROW = re.compile(
        r"(?is)(?:^|\n)\s*(?:Question|Answer|Source)\s*:\s*.+(?:\n\s*(?:Question|Answer|Source)\s*:)",
    )

    def check(self, text: str) -> bool:
        """Return True if text looks like leaked training/dataset content."""
        if not text:
            return False
        lower = text.lower()
        for item in self.BLOCKED:
            if item.lower() in lower:
                return True
        if self._DATASET_ROW.search(text):
            return True
        return False

    def detect(self, text: str) -> bool:
        return self.check(text)
