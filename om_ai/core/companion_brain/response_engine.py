"""Generate answers via ChatOrchestrator or chatgpt runtime."""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ResponseEngine:
    def generate(
        self,
        message: str,
        *,
        strategy: dict[str, Any],
        history: list[dict[str, Any]] | None,
        tenant_id: str,
        actor: str,
        model_generate: Callable[..., str] | None,
        model_context: str = "",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        engine = strategy.get("engine") or "chatgpt_runtime"
        extra = dict(extra or {})
        if model_context:
            extra.setdefault("companion_context", model_context[:2500])

        if engine == "chat_intelligence":
            from om_ai.core.chat_intelligence import run_chat_intelligence

            pack = run_chat_intelligence(
                message,
                history=history,
                tenant_id=tenant_id,
                actor=actor,
                model_generate=model_generate,
                model_context=model_context,
                extra=extra,
            ) or {}
            return {
                "answer": str(pack.get("answer") or ""),
                "source": "chat_intelligence",
                "pack": pack,
                "needs_model": pack.get("needs_model"),
            }

        from om_ai.core.chatgpt_runtime import run_chatgpt_runtime

        pack = run_chatgpt_runtime(
            message,
            history=history,
            tenant_id=tenant_id,
            actor=actor,
            model_generate=model_generate,
            extra=extra,
        ) or {}
        answer = str(pack.get("answer") or "")
        if not answer:
            ci = pack.get("chat_intelligence") or {}
            answer = str(ci.get("answer") or "")
        ci = pack.get("chat_intelligence") if isinstance(pack.get("chat_intelligence"), dict) else {}
        return {
            "answer": answer,
            "source": "chatgpt_runtime",
            "pack": pack,
            "needs_model": ci.get("needs_model"),
        }
