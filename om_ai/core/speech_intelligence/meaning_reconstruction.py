"""Reconstruct likely user meaning from partial + context (dynamic, not canned)."""
from __future__ import annotations

from typing import Any

from .sentence_completion import SentenceCompletion
from .speech_context import SpeechContext
from .uncertainty_detector import UncertaintyDetector


class MeaningReconstruction:
    def __init__(self) -> None:
        self.completion = SentenceCompletion()
        self.context = SpeechContext()
        self.uncertainty = UncertaintyDetector()

    def reconstruct(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        topic: str = "",
    ) -> dict[str, Any]:
        ctx = self.context.build(text, history=history, previous_topic=topic)
        done = self.completion.assess(text)
        unc = self.uncertainty.detect(text)
        continuing = bool(done.get("should_wait"))
        # Uncertainty softens style; only force wait when utterance is also incomplete
        if unc.get("prefer_listen") and not done.get("complete"):
            continuing = True
        goal = "continue_thought" if continuing else "express"
        if "?" in (text or ""):
            goal = "ask"
        low = (text or "").lower()
        if any(w in low for w in ("open", "search", "check", "analyze", "prepare", "kholo", "khoj")):
            if not continuing:
                goal = "act"
        return {
            "text": (text or "").strip(),
            "context": ctx,
            "completion": done,
            "uncertainty": unc,
            "user_continuing": continuing,
            "needs_listening": continuing or unc.get("prefer_listen"),
            "finished_enough": bool(done.get("complete")) and not unc.get("prefer_listen"),
            "inferred_goal": goal,
            "missing_information": continuing,
        }
