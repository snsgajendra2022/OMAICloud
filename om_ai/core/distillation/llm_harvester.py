"""Call connected teacher LLMs and collect raw responses."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_TEACHERS = ("gpt", "claude", "gemini", "qwen")

TEACHER_SYSTEM = (
    "You are a careful technical teacher. Give a complete, practical answer. "
    "Prefer concrete steps, architecture choices, and trade-offs. "
    "Do not invent fake citations."
)


class LLMHarvester:
    """Harvest answers from external teacher providers (API outputs only)."""

    def __init__(
        self,
        *,
        teachers: list[str] | tuple[str, ...] | None = None,
        chat_fn: Callable[..., tuple[str, str, str]] | None = None,
        stored_keys: dict[str, str] | None = None,
        max_tokens: int = 1200,
        temperature: float = 0.4,
        allow_mock: bool | None = None,
    ) -> None:
        self.teachers = [t.strip().lower() for t in (teachers or DEFAULT_TEACHERS) if t.strip()]
        self.chat_fn = chat_fn
        self.stored_keys = stored_keys or {}
        self.max_tokens = int(max_tokens)
        self.temperature = float(temperature)
        if allow_mock is None:
            allow_mock = os.getenv("OM_DISTILL_ALLOW_MOCK", "1").strip().lower() not in {
                "0",
                "false",
                "no",
                "off",
            }
        self.allow_mock = allow_mock

    def _chat(self) -> Callable[..., tuple[str, str, str]]:
        if self.chat_fn is not None:
            return self.chat_fn
        from om_ai.runtime.external_llms import chat_external

        return chat_external

    def _ready(self, provider_id: str) -> tuple[bool, str]:
        try:
            from om_ai.runtime.external_llms import provider_ready

            return provider_ready(provider_id, stored_keys=self.stored_keys)
        except Exception as exc:
            return False, str(exc)

    def _mock_answer(self, provider_id: str, task: str) -> str:
        # Deterministic offline stub so the pipeline can be tested without keys.
        topic = (task or "topic").strip().splitlines()[0][:120]
        flavors = {
            "gpt": (
                "Focus on clear layered design, API contracts, and operational runbooks.\n"
                "Cover tenant isolation, middleware, database strategy, permissions, and queues."
            ),
            "claude": (
                "Emphasize safety boundaries, audit trails, and readable architecture docs.\n"
                "Include auth, permissions, isolation, observability, and failure modes."
            ),
            "gemini": (
                "Prefer pragmatic MVP first: core paths, then scale knobs.\n"
                "Call out database sharding/tenancy, cache, network policy, and testing."
            ),
            "qwen": (
                "Provide stepwise implementation notes with trade-offs.\n"
                "Mention middleware, storage, encryption, deployment, and queue handling."
            ),
        }
        flavor = flavors.get(provider_id, "Provide a structured technical answer with trade-offs.")
        # Make weaker stub for ranking contrast when many teachers are mock.
        if provider_id.endswith("weak") or provider_id == "weak":
            return f"Short note on {topic}."
        return (
            f"Teacher view ({provider_id}) for: {topic}\n\n"
            f"{flavor}\n\n"
            "Recommended approach:\n"
            "1. Clarify requirements and constraints.\n"
            "2. Choose a clear architecture with isolation boundaries.\n"
            "3. Define middleware / auth / permissions.\n"
            "4. Plan data storage, queues, and observability.\n"
            "5. Ship an MVP, then harden security and scale.\n\n"
            "Common pitfalls: weak tenant isolation, shared secrets, missing audits."
        )

    def harvest(self, task: str, *, teachers: list[str] | None = None) -> dict[str, Any]:
        task = (task or "").strip()
        if not task:
            raise ValueError("task is required")
        ids = [t.strip().lower() for t in (teachers or self.teachers) if t.strip()]
        chat = self._chat()
        responses: list[dict[str, Any]] = []
        for pid in ids:
            ok, reason = self._ready(pid)
            entry: dict[str, Any] = {
                "provider": pid,
                "ok": False,
                "text": "",
                "model": "",
                "vendor": "",
                "error": "",
                "source": "live",
            }
            try:
                if not ok:
                    if self.allow_mock:
                        entry["text"] = self._mock_answer(pid, task)
                        entry["ok"] = True
                        entry["model"] = f"{pid}-mock"
                        entry["vendor"] = "mock"
                        entry["source"] = "mock"
                        entry["error"] = f"provider_not_ready:{reason}"
                    else:
                        entry["error"] = reason or "provider_not_ready"
                else:
                    text, display, vendor = chat(
                        pid,
                        [
                            {"role": "system", "content": TEACHER_SYSTEM},
                            {"role": "user", "content": task},
                        ],
                        stored_keys=self.stored_keys,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )
                    entry["text"] = str(text or "").strip()
                    entry["model"] = str(display or pid)
                    entry["vendor"] = str(vendor or pid)
                    entry["ok"] = bool(entry["text"])
                    if not entry["ok"]:
                        entry["error"] = "empty_response"
            except Exception as exc:
                logger.debug("teacher %s failed: %s", pid, exc)
                if self.allow_mock:
                    entry["text"] = self._mock_answer(pid, task)
                    entry["ok"] = True
                    entry["model"] = f"{pid}-mock"
                    entry["vendor"] = "mock"
                    entry["source"] = "mock"
                    entry["error"] = str(exc)
                else:
                    entry["error"] = str(exc)
            responses.append(entry)

        ok_count = sum(1 for r in responses if r.get("ok") and r.get("text"))
        return {
            "task": task,
            "teachers": ids,
            "responses": responses,
            "ok_count": ok_count,
            "live_count": sum(1 for r in responses if r.get("source") == "live" and r.get("ok")),
            "mock_count": sum(1 for r in responses if r.get("source") == "mock" and r.get("ok")),
        }
