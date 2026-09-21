"""Incomplete / partial speech — continue the story, never scold."""
from __future__ import annotations

import re
from typing import Any


class IncompleteSpeech:
    """
    User: "OM yesterday I was fixing my server but..."
    Robot: "Please complete your sentence."
    Friend: "You were fixing the server yesterday and something happened?
             Did you get stuck with an error or was there another issue?"
    """

    def understand(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        topic: str = "general",
        dialogue_blob: str = "",
    ) -> dict[str, Any]:
        text = (message or "").strip()
        incomplete = bool(
            re.search(
                r"(?:\.\.\.|…)\s*$|,\s*$|\bbut\s*$|\band\s*$|\bso\s*$|\bthen\s*$|"
                r"\bto\s*$|\bwith\s*$|\bbecause\s*$",
                text,
                re.I,
            )
        )
        if not incomplete and not text.endswith(("—", "-")):
            incomplete = bool(re.search(r"(?i)\b(but|and|so|then)\s+\w{0,12}$", text)) and len(
                text.split()
            ) >= 6 and "?" not in text

        if not incomplete:
            return {
                "incomplete": False,
                "completed_sense": text,
                "prediction": None,
                "friend_continue": None,
                "system_hint": "",
                "expected": None,
            }

        focus = self._extract_focus(text, history=history, topic=topic, dialogue_blob=dialogue_blob)
        yesterday = bool(re.search(r"(?i)\byesterday\b|\bwas (?:trying|fixing)\b", text))

        if focus in {"server", "bug", "api", "deploy", "build", "database", "code"}:
            if yesterday and focus == "server":
                continue_ask = (
                    "You were fixing the server yesterday and something happened? "
                    "Did you get stuck with an error or was there another issue?"
                )
            elif yesterday:
                continue_ask = (
                    f"You were fixing the {focus} yesterday and something happened? "
                    "Did you get stuck with an error or was there another issue?"
                )
            else:
                continue_ask = (
                    f"You were fixing the {focus} and something happened? "
                    "Did you get stuck with an error or was there another issue?"
                )
        elif focus:
            continue_ask = (
                f"You started talking about {focus}. What happened next?"
            )
        else:
            continue_ask = (
                "You started saying something — what happened next?"
            )

        return {
            "incomplete": True,
            "completed_sense": f"{text.rstrip('.…, ')} — (thought unfinished)",
            "prediction": "user wants to continue story",
            "focus": focus,
            "friend_continue": continue_ask,
            "expected": "continue_story",
            "system_hint": (
                "Partial thought detected. Mirror topic and invite the next beat. "
                "Never say 'please complete your sentence'."
            ),
        }

    def _extract_focus(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None,
        topic: str,
        dialogue_blob: str,
    ) -> str:
        low = text.lower()
        m = re.search(
            r"(?i)(?:fix(?:ing)?|debug|deploy|build|write|update|open|check)\s+"
            r"(?:the\s+|my\s+|that\s+)?(.{2,40}?)(?:\s+but|\s+and|\.\.\.|…|$)",
            text,
        )
        if m:
            chunk = m.group(1).strip(" .,").lower()
            for noun in ("server", "bug", "api", "deploy", "build", "database", "code"):
                if noun in chunk:
                    return noun
            return chunk[:40]
        for noun in ("server", "bug", "api", "deploy", "build", "database", "code"):
            if noun in low:
                return noun
        if topic and topic not in {"general", "day_life"}:
            return topic.replace("_", " ")
        blob = (dialogue_blob or "").lower()
        for noun in ("server", "bug", "project", "meeting"):
            if noun in blob:
                return noun
        if history:
            last = str((history[-1] or {}).get("content") or (history[-1] or {}).get("text") or "")
            for noun in ("server", "bug", "project"):
                if noun in last.lower():
                    return noun
        return ""
