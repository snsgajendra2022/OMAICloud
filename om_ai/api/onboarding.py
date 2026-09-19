"""
OM API Onboarding Controller

Dynamic first-time user bootstrap.

Responsibilities:
- Receive onboarding request
- Validate / normalize input
- Call OM onboarding engine
- Return structured response

Business logic lives in:
om_ai.core.onboarding
"""
from __future__ import annotations

import logging
from typing import Any

from om_ai.core.onboarding.onboarding_engine import (
    OMOnboardingEngine,
    get_onboarding_engine as _core_get_engine,
)

logger = logging.getLogger(__name__)

_engine = _core_get_engine()


def bootstrap_user_workspace(
    tenant_id: str,
    actor: str,
    *,
    display_name: str = "",
    profile: dict[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """
    Production onboarding entry point.

    Creates personalized OM environment:
    - User profile
    - Workspace
    - Assistant
    - Memory
    - Prompts
    - Companion configuration
    """
    try:
        tenant_id = (tenant_id or "default").strip() or "default"
        actor = (actor or "anonymous").strip() or "anonymous"
        display_name = (display_name or "User").strip() or "User"

        user_profile: dict[str, Any] = dict(profile) if profile else {}
        user_profile.update(
            {
                "display_name": display_name,
                "tenant_id": tenant_id,
                "actor": actor,
            }
        )

        logger.info("Starting OM onboarding user=%s", actor)
        result = _engine.bootstrap(
            tenant_id=tenant_id,
            actor=actor,
            profile=user_profile,
            force=force,
        )

        ok = str(result.get("status") or "") == "completed"
        out: dict[str, Any] = {
            "ok": ok,
            "user": actor,
            "display_name": display_name,
            "result": result,
        }
        if not ok:
            out["error"] = result.get("error") or "onboarding_failed"
        return out
    except Exception as exc:
        logger.exception("OM onboarding failed user=%s", actor)
        return {
            "ok": False,
            "error": str(exc),
            "user": actor,
        }


def get_onboarding_engine() -> OMOnboardingEngine:
    """Access singleton onboarding engine (API / tests / admin)."""
    return _core_get_engine()
