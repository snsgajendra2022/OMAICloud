"""STEP 30 — OM Brain Controller (ChatGPT-like runtime integration)."""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class OMBrainController:
    """
    React Chat / API
      → Chat Intelligence
      → Memory / Knowledge / Research / Agents
      → Intelligence Fusion
      → Response Intelligence
      → Quality Control
      → Final Answer
    """

    def __init__(self) -> None:
        self._ready = True

    def run(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        tenant_id: str = "default",
        actor: str = "",
        model_generate: Callable[..., str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stages: list[str] = ["om_brain_controller"]
        meta: dict[str, Any] = {"step": 30, "runtime": "chatgpt_like"}
        q = (message or "").strip()
        if not q:
            return {"answer": "", "stages": stages, "meta": meta}

        # 1) Chat Intelligence
        stages.append("chat_intelligence")
        chat: dict[str, Any] = {}
        try:
            from om_ai.core.chat_intelligence import run_chat_intelligence

            chat = run_chat_intelligence(
                q,
                history=history,
                tenant_id=tenant_id,
                actor=actor,
                model_generate=model_generate,
                extra=extra,
            ) or {}
            meta["chat_intelligence"] = {
                "intent": chat.get("intent"),
                "needs_model": chat.get("needs_model"),
                "stages": chat.get("stages"),
            }
            if chat.get("answer") and not chat.get("needs_model", True):
                stages.append("response")
                return {
                    "answer": chat["answer"],
                    "stages": stages,
                    "meta": meta,
                    "chat_intelligence": chat,
                    "source": "chat_intelligence",
                }
        except Exception as exc:
            meta["chat_intelligence"] = {"error": str(exc)}

        extra_d = dict(extra or {})
        voice_mode = bool(extra_d.get("voice_mode") or extra_d.get("skip_canned_social"))

        # 2) Brain router — text/dev path only. Voice never speaks agent dumps.
        stages.append("brain_router")
        brain: dict[str, Any] = {}
        if not voice_mode:
            try:
                from om_ai.core.brain_router import run_om_brain_router

                brain = run_om_brain_router(q, context={"history": history or [], **extra_d}) or {}
                meta["brain_router"] = {
                    "models": brain.get("models"),
                    "research_used": brain.get("research_used"),
                    "knowledge_found": brain.get("knowledge_found"),
                }
            except Exception as exc:
                meta["brain_router"] = {"error": str(exc)}
        else:
            meta["brain_router"] = {"skipped": "voice_mode"}

        draft = str(chat.get("answer") or "").strip()
        try:
            from om_ai.core.companion_personality.voice_presence import (
                is_garbage_spoken,
                strip_internal_chrome,
            )

            draft = strip_internal_chrome(draft)
            if is_garbage_spoken(draft):
                draft = ""
        except Exception:
            pass

        if not voice_mode:
            sol = str((chat.get("solution") or {}).get("answer") or "").strip()
            if sol and (not draft or len(sol) > len(draft)):
                draft = sol
            # Never promote agent context_blob to user-facing answer
            fusion = ""
            if isinstance(brain.get("fusion"), dict):
                fusion = str((brain.get("fusion") or {}).get("answer") or "").strip()
            if fusion and (not draft or len(fusion) > len(draft)):
                draft = fusion
            brain_ans = str(brain.get("answer") or "").strip()
            if brain_ans and not draft:
                draft = brain_ans


        # 3) Response Intelligence
        stages.append("response_intelligence")
        resp: dict[str, Any] = {}
        if not voice_mode:
            try:
                from om_ai.core.response.response_intelligence import run_response_intelligence

                intent = str((chat.get("intent") or {}).get("intent") or "")
                strategy = str((chat.get("plan") or {}).get("strategy") or "")
                resp = run_response_intelligence(q, draft, intent=intent, strategy=strategy) or {}
                draft = str(resp.get("answer") or draft)
                meta["response_intelligence"] = {
                    "kind": resp.get("kind"),
                    "strategy": resp.get("strategy"),
                    "improved": resp.get("improved"),
                }
            except Exception as exc:
                meta["response_intelligence"] = {"error": str(exc)}
        else:
            meta["response_intelligence"] = {"skipped": "voice_mode"}

        # 4) Continuous learning observe
        stages.append("continuous_learning")
        try:
            from om_ai.core.continuous_learning import run_continuous_learning

            learn = run_continuous_learning(
                q,
                draft,
                quality=(resp.get("fact_check") if isinstance(resp, dict) else None),
            )
            meta["continuous_learning"] = {
                "failed": bool(((learn.get("observed") or {}).get("analysis") or {}).get("failed")),
                "gaps": ((learn.get("observed") or {}).get("gaps") or {}).get("total"),
            }
        except Exception as exc:
            meta["continuous_learning"] = {"error": str(exc)}

        stages.append("response")
        if not draft:
            draft = ""
        return {
            "answer": draft,
            "stages": stages,
            "meta": meta,
            "chat_intelligence": chat,
            "brain_router": brain,
            "response_intelligence": resp,
            "context_blob": str(brain.get("context_blob") or ""),
            "source": "om_brain_controller",
            "status": {"ready": True, "step": 30},
        }


def run_om_brain_controller(message: str, **kwargs: Any) -> dict[str, Any]:
    return OMBrainController().run(message, **kwargs)
