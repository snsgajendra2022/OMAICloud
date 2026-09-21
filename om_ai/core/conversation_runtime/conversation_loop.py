"""Full conversation loop tying presence + realtime + human layer."""
from __future__ import annotations

from typing import Any, Callable

from .realtime_conversation import RealtimeConversation


class ConversationLoop:
    def __init__(self) -> None:
        self.realtime = RealtimeConversation()
        self._presence = None
        self._human = None

    def bind(
        self,
        *,
        stop_speech: Callable[[], None] | None = None,
        presence=None,
        human_pipeline=None,
    ) -> None:
        self.realtime.bind_stop(stop_speech)
        self._presence = presence
        self._human = human_pipeline

    def partial(self, text: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if self._presence is not None:
            try:
                self._presence.listening()
            except Exception:
                pass
        return self.realtime.on_partial(text, history=history)

    def final_turn(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        generate: Callable[..., str] | None = None,
        profile: dict[str, Any] | None = None,
        memory_blob: str = "",
        locale: str = "en",
    ) -> dict[str, Any]:
        rt = self.realtime.on_final(text, history=history)
        if rt.get("interrupted"):
            if self._presence is not None:
                try:
                    self._presence.interrupt()
                except Exception:
                    pass
            return {**rt, "answer": "", "handled": True}

        if self._presence is not None:
            try:
                self._presence.thinking()
            except Exception:
                pass

        human_out: dict[str, Any] = {}
        if self._human is not None:
            try:
                human_out = self._human.run(
                    text,
                    history=history,
                    memory_blob=memory_blob,
                    profile=profile,
                    locale=locale,
                    generate=generate,
                )
            except Exception as exc:
                human_out = {"error": str(exc)}

        if self._presence is not None:
            try:
                self._presence.responding()
                self.realtime.on_speaking(True)
            except Exception:
                pass

        answer = str(human_out.get("answer") or human_out.get("spoken") or "")
        return {
            **rt,
            "human": human_out,
            "answer": answer,
            "spoken": answer,
            "handled": True,
            "presence_phase": "responding",
        }

    def after_speech(self) -> dict[str, Any]:
        self.realtime.on_speaking(False)
        if self._presence is not None:
            try:
                return self._presence.waiting()
            except Exception:
                pass
        return {"phase": "waiting"}
