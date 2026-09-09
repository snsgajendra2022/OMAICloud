from dataclasses import dataclass


@dataclass
class MessageReadResult:
    original_text: str
    normalized_text: str
    paragraphs: list[str]
    sentences: list[str]
    word_count: int
    character_count: int


class MessageReader:

    def read(self, text: str) -> MessageReadResult:

        if not isinstance(text, str):
            text = str(text or "")

        original = text.strip()

        normalized = " ".join(
            original.split()
        )

        paragraphs = [
            p.strip()
            for p in original.split("\n")
            if p.strip()
        ]

        sentences = self._split_sentences(
            normalized
        )

        return MessageReadResult(
            original_text=original,
            normalized_text=normalized,
            paragraphs=paragraphs,
            sentences=sentences,
            word_count=len(
                normalized.split()
            ),
            character_count=len(original)
        )


    def _split_sentences(
        self,
        text: str
    ) -> list[str]:

        import re

        if not text:
            return []

        parts = re.split(
            r"(?<=[.!?।！？])\s+",
            text
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]