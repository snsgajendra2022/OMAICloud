"""Build structured OM-1.0 Genesis assistant answers."""
from __future__ import annotations

from .domains import ARCHITECTURE_SECTIONS, GENESIS_SYSTEM


def architecture_answer(
    *,
    title: str,
    understanding: str,
    components: list[str],
    data_flow: list[str],
    stack: list[str],
    roadmap: list[str],
    risks: list[str],
    future: list[str],
    horizon_note: str = "",
) -> str:
    parts = [
        f"## 1. Understanding\n{understanding.strip()}",
        f"## 2. System Architecture\n**{title}**\n\n"
        + "\n".join(f"- {c}" for c in components[:3])
        + "\n\n```text\n"
        + " → ".join(data_flow)
        + "\n```",
        "## 3. Components\n" + "\n".join(f"- {c}" for c in components),
        "## 4. Data Flow\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(data_flow)),
        "## 5. Technology Stack\n" + "\n".join(f"- {s}" for s in stack),
        "## 6. Implementation Roadmap\n" + "\n".join(f"- {r}" for r in roadmap),
        "## 7. Risks\n" + "\n".join(f"- {r}" for r in risks),
        "## 8. Future Expansion\n" + "\n".join(f"- {f}" for f in future),
    ]
    if horizon_note:
        parts.append(f"## Horizon\n{horizon_note.strip()}")
    return "\n\n".join(parts)


def explain_answer(*, topic: str, body: str, horizon: str) -> str:
    label = {
        "current": "Current technology",
        "near_future": "Near-future research / engineering",
        "research": "Long-term research concept (not production today)",
    }.get(horizon, horizon)
    return (
        f"## Topic\n{topic}\n\n"
        f"## Explanation\n{body.strip()}\n\n"
        f"## Horizon\n**{label}**\n\n"
        "## Practical next step\n"
        "Map this to OM AI modules first (software/agents/memory), "
        "then hardware contracts, then research programs only when labs/safety are ready."
    )


def make_sft_row(
    *,
    instruction: str,
    output: str,
    domain: str,
    horizon: str,
    tags: list[str] | None = None,
) -> dict:
    return {
        "system": GENESIS_SYSTEM,
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip(),
        "domain": domain,
        "horizon": horizon,
        "tags": tags or [],
        "format": "omai-genesis-sft-v1",
    }


__all__ = [
    "ARCHITECTURE_SECTIONS",
    "architecture_answer",
    "explain_answer",
    "make_sft_row",
]
