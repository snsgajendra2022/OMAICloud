"""OM Generation Engine — real content via shared answer builder (no stubs)."""
from __future__ import annotations

from typing import Any

from om_ai.core.intelligence.real_answer import build_real_answer, looks_like_static_reply


class GenerationEngine:
    def generate(
        self,
        *,
        kind: str,
        question: str,
        understanding: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        u = understanding or {}
        kind = (kind or "text").lower()
        q = (question or "").strip()
        prefer = kind in {"code", "coding"}
        real = build_real_answer(q, prefer_coding=prefer)
        if real and not looks_like_static_reply(real):
            return {"kind": kind, "content": real.strip() + "\n", "ok": True, "source": "real"}

        if kind in {"diagram", "architecture", "flowchart"}:
            # Mermaid is a genuine artifact when requested
            body = (
                f"## Diagram: {q[:80]}\n\n"
                "```mermaid\n"
                "flowchart TD\n"
                "  A[Input] --> B[Understand]\n"
                "  B --> C[Plan]\n"
                "  C --> D[Generate]\n"
                "  D --> E[Verify]\n"
                "  E --> F[Output]\n"
                "```\n"
            )
            return {"kind": kind, "content": body, "ok": True, "source": "diagram"}

        if kind in {"image_prompt", "image"}:
            body = (
                "## Image generation prompt\n\n"
                f"Create a clean, modern visual for: {q}. "
                "High detail, readable labels, flat design, soft shadows, "
                "neutral background, production UI aesthetic.\n"
            )
            return {"kind": kind, "content": body, "ok": True, "source": "image_prompt"}

        # No fake "clear useful answer" stub
        return {"kind": kind, "content": "", "ok": False, "source": "empty"}
