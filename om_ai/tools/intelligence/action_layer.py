"""
Autonomous Action Layer — STEP 86 facade.

Architecture:
  User → Reasoning hints → Tool Decision → Permission → Execution → Analysis → Response
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from .audit import ActionAuditLog
from .decision_engine import ToolDecision, ToolDecisionEngine
from .executor import ActionExecutor
from .permission_gate import ActionPermissionGate, PermissionVerdict
from .result_analyzer import ActionAnalysis, ResultAnalyzer


def action_layer_enabled() -> bool:
    return os.environ.get("OM_ACTION_LAYER", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


@dataclass
class ActionResult:
    mode: str
    needs_tools: bool
    tools_planned: list[str] = field(default_factory=list)
    tools_allowed: list[str] = field(default_factory=list)
    tools_blocked: list[str] = field(default_factory=list)
    execution: dict[str, Any] = field(default_factory=dict)
    analysis: ActionAnalysis | None = None
    decision: ToolDecision | None = None
    permissions: list[PermissionVerdict] = field(default_factory=list)
    response_context: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "needs_tools": self.needs_tools,
            "tools_planned": self.tools_planned,
            "tools_allowed": self.tools_allowed,
            "tools_blocked": self.tools_blocked,
            "execution": {
                "executed": (self.execution or {}).get("executed"),
                "ok": (self.execution or {}).get("ok"),
                "combined_len": len(str((self.execution or {}).get("combined_text") or "")),
            },
            "analysis": {
                "sufficient": self.analysis.sufficient if self.analysis else None,
                "summary": self.analysis.summary if self.analysis else None,
                "next_action": self.analysis.next_action if self.analysis else None,
                "confidence": self.analysis.confidence if self.analysis else None,
            }
            if self.analysis
            else None,
            "decision": {
                "reason": self.decision.reason if self.decision else None,
                "confidence": self.decision.confidence if self.decision else None,
                "risk": self.decision.risk if self.decision else None,
            }
            if self.decision
            else None,
            "response_context": self.response_context[:2000],
            "meta": self.meta,
        }


class AutonomousActionLayer:
    """Move OM from Answering AI → Action AI (controlled)."""

    def __init__(
        self,
        *,
        identity: str = "default",
        audit: ActionAuditLog | None = None,
    ) -> None:
        self.decision_engine = ToolDecisionEngine()
        self.permission = ActionPermissionGate(identity=identity)
        self.executor = ActionExecutor()
        self.analyzer = ResultAnalyzer()
        self.audit = audit or ActionAuditLog()
        self.identity = identity

    def run(
        self,
        question: str,
        *,
        context: dict[str, Any] | None = None,
        intent: dict[str, Any] | None = None,
        capability: dict[str, Any] | None = None,
        understanding: dict[str, Any] | None = None,
    ) -> ActionResult:
        ctx = dict(context or {})
        actor = str(ctx.get("actor") or self.identity)
        has_attachment = bool(ctx.get("image_path") or ctx.get("attachment"))

        if not action_layer_enabled():
            return ActionResult(
                mode="disabled",
                needs_tools=False,
                meta={"reason": "OM_ACTION_LAYER=0"},
            )

        decision = self.decision_engine.decide(
            question,
            intent=intent,
            capability=capability,
            understanding=understanding,
            has_attachment=has_attachment,
        )

        if not decision.needs_tools:
            self.audit.record(
                {
                    "event": "decision",
                    "actor": actor,
                    "question": (question or "")[:200],
                    "needs_tools": False,
                    "reason": decision.reason,
                }
            )
            return ActionResult(
                mode=decision.mode,
                needs_tools=False,
                decision=decision,
                tools_planned=[],
                analysis=self.analyzer.analyze(question, {}, decision_mode="answer"),
                meta={"reason": decision.reason},
            )

        allowed, verdicts = self.permission.filter_allowed(
            decision.tools,
            question,
            context=ctx,
        )
        blocked = [v.tool for v in verdicts if not v.allowed]

        execution: dict[str, Any] = {
            "executed": [],
            "results": [],
            "texts": [],
            "combined_text": "",
            "ok": False,
        }
        if allowed:
            execution = self.executor.execute(allowed, question, context=ctx)

        analysis = self.analyzer.analyze(
            question,
            execution,
            decision_mode=decision.mode,
        )
        response_context = str(
            execution.get("context_block")
            or execution.get("combined_text")
            or ""
        ).strip()

        self.audit.record(
            {
                "event": "action",
                "actor": actor,
                "question": (question or "")[:200],
                "planned": decision.tools,
                "allowed": allowed,
                "blocked": blocked,
                "executed": execution.get("executed"),
                "ok": execution.get("ok"),
                "analysis": analysis.summary,
            }
        )

        return ActionResult(
            mode=decision.mode,
            needs_tools=True,
            tools_planned=list(decision.tools),
            tools_allowed=allowed,
            tools_blocked=blocked,
            execution=execution,
            analysis=analysis,
            decision=decision,
            permissions=verdicts,
            response_context=response_context,
            meta={
                "reason": decision.reason,
                "risk": decision.risk,
                "confidence": decision.confidence,
            },
        )
