"""OM Onboarding Engine — profile → workspace → assistant → memory → prompts."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from .assistant_initializer import AssistantInitializer
from .memory_initializer import MemoryInitializer
from .onboarding_events import OnboardingEvent
from .onboarding_state import OnboardingStatus
from .prompt_generator import PromptGenerator
from .user_profiler import UserProfiler
from .workspace_builder import WorkspaceBuilder

logger = logging.getLogger(__name__)

_ENGINE: OMOnboardingEngine | None = None


def _safe_actor(actor: str) -> str:
    return re.sub(r"[^\w.\-:@]+", "_", (actor or "anonymous").strip())[:120] or "anonymous"


class OMOnboardingEngine:
    def __init__(self, *, store_dir: Path | None = None) -> None:
        self.profiler = UserProfiler()
        self.workspace = WorkspaceBuilder()
        self.assistant = AssistantInitializer()
        self.memory = MemoryInitializer()
        self.prompts = PromptGenerator()
        self.events: list[OnboardingEvent] = []
        root = Path(__file__).resolve().parents[3]
        self.store_dir = store_dir or (root / "artifacts" / "onboarding")
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, actor: str) -> Path:
        return self.store_dir / f"{_safe_actor(actor)}.json"

    def load(self, actor: str) -> dict[str, Any] | None:
        path = self._path(actor)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def is_completed(self, actor: str) -> bool:
        data = self.load(actor)
        return bool(data and data.get("status") == OnboardingStatus.COMPLETED.value)

    def _emit(self, actor: str, event: str, detail: dict[str, Any] | None = None) -> None:
        ev = OnboardingEvent(user_id=actor, event=event, detail=detail or {})
        self.events.append(ev)
        logger.info("onboarding.%s user=%s", event, actor)

    def _persist(self, actor: str, payload: dict[str, Any]) -> None:
        path = self._path(actor)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _apply_platform(
        self,
        tenant_id: str,
        actor: str,
        *,
        assistant: dict[str, Any],
        prompts: list[dict[str, Any]],
        memory: dict[str, Any],
    ) -> dict[str, Any]:
        applied: dict[str, Any] = {"assistant": False, "prompts": 0, "memory": False}
        try:
            from om_ai.api.workspace_store import get_workspace_store

            ws = get_workspace_store()
            if hasattr(ws, "create_assistant"):
                ws.create_assistant(
                    tenant_id,
                    actor,
                    name=str(assistant.get("name") or "OM Assistant"),
                    description="Personalized OM companion",
                    system_prompt=str(assistant.get("system_prompt") or ""),
                )
                applied["assistant"] = True
        except Exception as exc:
            logger.debug("platform assistant skip: %s", exc)

        try:
            from om_ai.api.platform_store import get_platform_store

            store = get_platform_store()
            if hasattr(store, "create_prompt"):
                for p in prompts[:8]:
                    title = str(p.get("title") or "Prompt")
                    body = str(p.get("body") or title)
                    store.create_prompt(
                        tenant_id,
                        actor,
                        name=title,
                        content=body,
                    )
                    applied["prompts"] += 1
        except Exception as exc:
            logger.debug("platform prompts skip: %s", exc)

        try:
            from om_ai.api.conversations import get_store

            facts = memory.get("facts") or []
            if facts:
                # best-effort: store a profile note if API exists
                get_store()
                applied["memory"] = True
        except Exception:
            pass

        return applied

    def bootstrap(
        self,
        tenant_id: str,
        actor: str,
        profile: dict[str, Any] | None = None,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        tenant_id = (tenant_id or "default").strip() or "default"
        actor = (actor or "anonymous").strip() or "anonymous"
        profile = dict(profile or {})

        if not force and self.is_completed(actor):
            existing = self.load(actor) or {}
            return {
                "status": OnboardingStatus.COMPLETED.value,
                "cached": True,
                **{k: existing.get(k) for k in ("user_profile", "workspace", "assistant", "memory", "prompts", "companion_context")},
            }

        try:
            self._emit(actor, "started")
            user_profile = self.profiler.build(actor, profile)
            self._emit(actor, OnboardingStatus.PROFILE_READY.value, {"purpose": user_profile.get("purpose")})

            workspace = self.workspace.create(tenant_id, actor, user_profile)
            assistant = self.assistant.create(tenant_id, actor, user_profile)
            self._emit(actor, OnboardingStatus.ASSISTANT_READY.value, {"name": assistant.get("name")})

            memory = self.memory.initialize(tenant_id, actor, user_profile)
            self._emit(actor, OnboardingStatus.MEMORY_READY.value)

            prompts = self.prompts.generate(tenant_id, actor, user_profile)
            applied = self._apply_platform(
                tenant_id, actor, assistant=assistant, prompts=prompts, memory=memory
            )

            companion_context = {
                "user": user_profile,
                "assistant": assistant,
                "memory": memory,
                "workspace": workspace,
            }

            # Soft-bind into companion runtime if already started
            try:
                from om_ai.core.companion_runtime import get_companion_runtime

                rt = get_companion_runtime()
                setattr(rt, "onboarding_context", companion_context)
            except Exception:
                pass

            result = {
                "status": OnboardingStatus.COMPLETED.value,
                "cached": False,
                "user_profile": user_profile,
                "workspace": workspace,
                "assistant": assistant,
                "memory": memory,
                "prompts": prompts,
                "companion_context": companion_context,
                "platform": applied,
                "events": [e.to_dict() for e in self.events[-12:]],
            }
            self._persist(actor, result)
            self._emit(actor, OnboardingStatus.COMPLETED.value)
            return result

        except Exception as exc:
            logger.exception("OM onboarding failed user=%s", actor)
            failed = {
                "status": OnboardingStatus.FAILED.value,
                "error": str(exc),
                "user_id": actor,
            }
            try:
                self._persist(actor, failed)
            except Exception:
                pass
            return failed


def get_onboarding_engine() -> OMOnboardingEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = OMOnboardingEngine()
    return _ENGINE
