"""Intent understanding adapter."""
from __future__ import annotations

import re
from typing import Any


class IntentUnderstanding:
    def infer(self, message: str) -> dict[str, Any]:
        low = (message or "").lower().strip()
        if re.search(r"(?i)\b(search|google|khoj|research)\b", low):
            return {"intent": "research", "needs": "information"}
        if re.search(r"(?i)\b(open|kholo|launch|start)\b", low):
            return {"intent": "action", "needs": "permission"}
        if re.search(r"(?i)\b(tired|sad|bad day|stress|angry|lonely|thak|udas)\b", low):
            return {"intent": "sharing", "needs": "conversation", "action": "listen"}
        if re.search(r"(?i)\b(hi|hello|hey|namaste)\b", low):
            return {"intent": "greeting", "needs": "presence"}
        if "?" in (message or "") or re.search(r"(?i)\b(what|how|why|kaise|kya)\b", low):
            return {"intent": "question", "needs": "answer"}
        return {"intent": "conversation", "needs": "assist"}
