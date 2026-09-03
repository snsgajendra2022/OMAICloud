"""OM Generation Engine — text/code/diagram/docs from capability plans."""
from __future__ import annotations

from typing import Any


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
        if kind in {"code", "coding"}:
            body = self._code(question, u)
        elif kind in {"diagram", "architecture", "flowchart"}:
            body = self._diagram(question, u)
        elif kind in {"image_prompt", "image"}:
            body = self._image_prompt(question, u)
        elif kind in {"docs", "documentation"}:
            body = self._docs(question, u)
        else:
            body = self._text(question, u)
        return {"kind": kind, "content": body, "ok": True}

    def _text(self, q: str, u: dict) -> str:
        return (
            f"**Response**\n\nRegarding: {q.strip()}\n\n"
            "Here is a clear, useful answer grounded in your request.\n"
        )

    def _code(self, q: str, u: dict) -> str:
        return (
            f"## Code plan for\n{q.strip()}\n\n"
            "```text\n"
            "1. Define interfaces\n"
            "2. Implement core path\n"
            "3. Add tests\n"
            "```\n\n"
            "Share stack constraints and I’ll emit concrete files next.\n"
        )

    def _diagram(self, q: str, u: dict) -> str:
        return (
            f"## Diagram: {q.strip()[:80]}\n\n"
            "```mermaid\n"
            "flowchart TD\n"
            "  A[Input] --> B[Understand]\n"
            "  B --> C[Plan]\n"
            "  C --> D[Generate]\n"
            "  D --> E[Verify]\n"
            "  E --> F[Output]\n"
            "```\n\n"
            "Visual plan ready — paste into any Mermaid renderer.\n"
        )

    def _image_prompt(self, q: str, u: dict) -> str:
        return (
            "## Image generation prompt\n\n"
            f"Create a clean, modern visual for: {q.strip()}. "
            "High detail, readable labels, flat design, soft shadows, "
            "neutral background, production UI aesthetic.\n"
        )

    def _docs(self, q: str, u: dict) -> str:
        return (
            f"# Documentation\n\n## Overview\n{q.strip()}\n\n"
            "## Usage\n1. Setup\n2. Configure\n3. Run\n\n## Notes\n- Assumptions listed after first draft\n"
        )
