"""Clean → verify → store knowledge (never training on raw dumps alone)."""
from __future__ import annotations

import re
from typing import Any

from .distillation_state import DistillationState


_TOOL_LEAK = re.compile(r"\[tool:[^\]]+\]", re.I)
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


class KnowledgeCollector:
    """Pipeline: Raw → Cleaning → Verification → store artifacts."""

    def __init__(self, state: DistillationState | None = None) -> None:
        self.state = state or DistillationState()

    def clean_text(self, text: str) -> str:
        t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        t = _TOOL_LEAK.sub("", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        lines = [_MULTI_SPACE.sub(" ", ln).rstrip() for ln in t.split("\n")]
        return "\n".join(lines).strip()

    def verify(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        issues: list[str] = []
        if len(t) < 40:
            issues.append("too_short")
        if _TOOL_LEAK.search(t):
            issues.append("tool_leak")
        if re.search(r"(password\s*=\s*|api[_-]?key\s*[:=])\s*\S+", t, re.I):
            issues.append("possible_secret")
        # Extremely repetitive
        words = re.findall(r"[a-zA-Z]+", t.lower())
        if words:
            top = max(words.count(w) for w in set(words))
            if top > max(12, len(words) // 4):
                issues.append("repetitive")
        return {"ok": not issues, "issues": issues}

    def process_harvest(self, harvest: dict[str, Any], *, run_id: str) -> dict[str, Any]:
        task = str(harvest.get("task") or "")
        cleaned_responses: list[dict[str, Any]] = []
        for r in harvest.get("responses") or []:
            raw = str(r.get("text") or "")
            cleaned = self.clean_text(raw)
            ver = self.verify(cleaned)
            item = {
                **r,
                "raw": raw,
                "cleaned": cleaned if ver["ok"] else "",
                "verification": ver,
                "ok": bool(r.get("ok")) and ver["ok"] and bool(cleaned),
            }
            if not ver["ok"]:
                item["error"] = ",".join(ver["issues"]) or item.get("error") or "verify_failed"
            cleaned_responses.append(item)

        pack = {
            "run_id": run_id,
            "task": task,
            "teachers": harvest.get("teachers") or [],
            "responses": cleaned_responses,
            "ok_count": sum(1 for x in cleaned_responses if x.get("ok")),
            "live_count": harvest.get("live_count"),
            "mock_count": harvest.get("mock_count"),
            "stage": "cleaned_verified",
        }
        raw_path = self.state.raw_dir / f"{run_id}.json"
        clean_path = self.state.clean_dir / f"{run_id}.json"
        self.state.write_json(
            raw_path,
            {
                "run_id": run_id,
                "task": task,
                "responses": [
                    {
                        "provider": r.get("provider"),
                        "model": r.get("model"),
                        "source": r.get("source"),
                        "text": r.get("raw") or r.get("text"),
                        "error": r.get("error"),
                    }
                    for r in cleaned_responses
                ],
            },
        )
        self.state.write_json(clean_path, pack)
        pack["raw_path"] = str(raw_path)
        pack["clean_path"] = str(clean_path)
        return pack
