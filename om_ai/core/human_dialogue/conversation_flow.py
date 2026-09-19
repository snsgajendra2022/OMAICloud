from __future__ import annotations
from .natural_response import NaturalResponse

class ConversationFlow:
    def __init__(self) -> None:
        self.natural = NaturalResponse()

    def reply(self, text: str, *, address: str = "Sir", locale: str = "en") -> str | None:
        intent = self.natural.detect(text)
        return self.natural.for_intent(intent, address=address, locale=locale)
