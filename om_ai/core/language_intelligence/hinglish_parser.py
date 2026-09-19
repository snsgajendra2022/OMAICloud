from __future__ import annotations
import re
from typing import Any

class HinglishParser:
    """Semantic-ish parse for common Hinglish goals (reminder, open, continue)."""

    def parse(self, text: str) -> dict[str, Any]:
        low = (text or "").lower()
        raw = text or ""
        out: dict[str, Any] = {"raw": text, "slots": {}}

        # Reminder: "kal mujhe yaad dilana ki project complete karna hai"
        if re.search(r"(?i)(yaad\s*dila|remind|याद)", low) or "याद" in raw:
            out["intent"] = "create_reminder"
            when = "tomorrow" if re.search(r"(?i)\b(kal|tomorrow)\b", low) or "कल" in raw else "unspecified"
            task = text
            m = re.search(r"(?i)(?:ki|that)\s+(.+)$", text.strip())
            if m:
                task = m.group(1).strip()
            out["slots"] = {"when": when, "task": task}
            out["confidence"] = 0.85
            return out

        if re.search(r"(?i)(continue|aage|pehle wala|jahan chhora)", low):
            out["intent"] = "continue_work"
            out["slots"] = {"domain": "project"}
            out["confidence"] = 0.75
            return out

        if re.search(r"(?i)(open|kholo|launch).*(code|vscode|project)", low):
            out["intent"] = "open_editor"
            out["confidence"] = 0.8
            return out

        out["intent"] = "converse"
        out["confidence"] = 0.4
        return out
