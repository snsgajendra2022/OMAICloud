"""Regenerate when validation fails — capability re-run or clarification."""
from __future__ import annotations

from typing import Any


class SelfCorrection:
    def correct(
        self,
        question: str,
        previous: str,
        validation: dict[str, Any],
        *,
        router: Any,
        capability: dict[str, Any],
        context: dict[str, Any],
        understanding: dict[str, Any],
        intent: dict[str, Any],
    ) -> str:
        issues = validation.get("issues") or []
        # Echo / wrong intent → force clarify or re-execute primary capability
        if validation.get("needs_clarification") or understanding.get("intent") == "unclear":
            clarify = router.route({"intent": "unclear", "canonical": "unclear"})
            return router.execute(clarify, question, context, understanding)

        # Re-run capability once
        retry = router.execute(capability, question, context, understanding)
        if retry.strip() and retry.strip() != previous.strip():
            return retry

        # Last resort: empty → chat falls through to Absolute OS / model / brain
        return ""
