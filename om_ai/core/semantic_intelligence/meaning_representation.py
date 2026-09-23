"""Meaning representation — structured frame of what the user meant."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MeaningFrame:
    text: str = ""
    corrected: str = ""
    intent: str = "conversation"
    goal: str = "continue"
    speech_act: str = "statement"  # statement | question | request | share | command
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    polarity: str = "neutral"  # positive | negative | neutral
    confidence: float = 0.6
    needs_clarification: bool = False
    listen_first: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MeaningRepresentation:
    """Build / merge meaning frames."""

    def build(
        self,
        *,
        text: str,
        corrected: str = "",
        intent: str = "conversation",
        goal: str = "continue",
        speech_act: str = "statement",
        entities: list[str] | None = None,
        topics: list[str] | None = None,
        polarity: str = "neutral",
        confidence: float = 0.6,
        needs_clarification: bool = False,
        listen_first: bool = False,
        **meta: Any,
    ) -> MeaningFrame:
        return MeaningFrame(
            text=(text or "").strip(),
            corrected=(corrected or text or "").strip(),
            intent=intent,
            goal=goal,
            speech_act=speech_act,
            entities=list(entities or []),
            topics=list(topics or []),
            polarity=polarity,
            confidence=float(confidence),
            needs_clarification=bool(needs_clarification),
            listen_first=bool(listen_first),
            meta=dict(meta),
        )

    def merge(self, base: MeaningFrame, overlay: dict[str, Any] | None = None) -> MeaningFrame:
        overlay = overlay or {}
        data = base.to_dict()
        for k, v in overlay.items():
            if k == "meta" and isinstance(v, dict):
                data["meta"] = {**(data.get("meta") or {}), **v}
            elif v is not None and v != "":
                data[k] = v
        return MeaningFrame(**{k: data[k] for k in MeaningFrame.__dataclass_fields__})
