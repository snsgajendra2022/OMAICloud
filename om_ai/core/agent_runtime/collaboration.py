"""Agent collaboration helpers for STEP 26."""
from __future__ import annotations

from typing import Any

from .communication import RuntimeCommunication


class AgentCollaboration:
    """Coordinate multi-agent teamwork on a shared goal."""

    def __init__(self, communication: RuntimeCommunication | None = None) -> None:
        self.communication = communication or RuntimeCommunication()

    def form_team(self, roles: list[str]) -> dict[str, Any]:
        members = list(dict.fromkeys(roles or ["research", "quality"]))
        lead = members[0]
        return {
            "lead": lead,
            "members": members,
            "size": len(members),
        }

    def collaborate(
        self,
        task: str,
        roles: list[str],
        *,
        results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        team = self.form_team(roles)
        msgs = self.communication.broadcast(
            team["lead"],
            [m for m in team["members"] if m != team["lead"]],
            f"Collaborate on: {(task or '')[:240]}",
            kind="collab",
        )
        summary_parts = []
        for r in results or []:
            if not isinstance(r, dict):
                continue
            agent = r.get("type") or r.get("agent") or "agent"
            analysis = r.get("analysis") or r.get("result") or r.get("status")
            if analysis:
                summary_parts.append(f"{agent}: {analysis}")
        summary = "; ".join(summary_parts)[:2000] if summary_parts else (
            f"Team[{','.join(team['members'])}] ready for: {(task or '')[:160]}"
        )
        return {
            "team": team,
            "messages": msgs,
            "summary": summary,
            "result_count": len(results or []),
        }
