from __future__ import annotations
from typing import Any
from .monitoring_engine import MonitoringEngine
from .reminder_engine import ReminderEngine
from .suggestion_engine import SuggestionEngine

_RT = None

class BackgroundBrainRuntime:
    def __init__(self) -> None:
        self.reminders = ReminderEngine()
        self.monitor = MonitoringEngine()
        self.suggestions = SuggestionEngine()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 59, "name": "Background Proactive Intelligence"}

    def tick(self, *, last_focus: str = "", topic: str = "") -> dict[str, Any]:
        due = self.reminders.due()
        hints = self.monitor.health_hints()
        proactive = []
        if due:
            proactive.append(f"Reminder: {due[0]['text']}")
        if last_focus:
            proactive.append(self.suggestions.morning(last_focus=last_focus))
        elif topic:
            s = self.suggestions.from_context(topic)
            if s:
                proactive.append(s)
        return {"due_reminders": due, "health_hints": hints, "proactive": proactive}


def get_background_brain() -> BackgroundBrainRuntime:
    global _RT
    if _RT is None:
        _RT = BackgroundBrainRuntime()
    return _RT
