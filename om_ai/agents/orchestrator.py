"""
AgentOrchestrator: multi-step goal execution engine.

Features:
- Pluggable LLM engine (object with .generate(prompt, **kw) -> str)
- Pluggable RAG knowledge base and memory store
- Tool registry with risk levels and permission filtering
- Require-approval gate for high-risk tools
- Full analyze → plan → execute → observe → verify → finish loop
- Retries per step; never infinite-loops
- Audit log persisted to optional SQLite path
- Wall-clock budget (timeout_seconds)
- Roles: researcher, planner, executor, verifier, coding, business, document, communication
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from om_ai.reasoning import LLMPlanner, Plan, PlanStep, RulePlanner, StepStatus

logger = logging.getLogger(__name__)

# ─── Risk levels ──────────────────────────────────────────────────────────────

RiskLevel = str  # 'low' | 'medium' | 'high' | 'critical'

# ─── Tool registration record ─────────────────────────────────────────────────


@dataclass
class ToolEntry:
    tool: Any          # anything with .run(**kwargs) -> ToolResult
    risk_level: RiskLevel = "low"
    description: str = ""


# ─── Audit record ─────────────────────────────────────────────────────────────


@dataclass
class AuditEntry:
    run_id: str
    tenant_id: str
    user_id: str
    goal: str
    step_index: int
    step_description: str
    tool: str | None
    arguments: dict
    result: Any
    status: str
    elapsed_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─── Audit SQLite schema ──────────────────────────────────────────────────────

_AUDIT_DDL = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS agent_audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT    NOT NULL,
    tenant_id       TEXT    NOT NULL,
    user_id         TEXT    NOT NULL,
    goal            TEXT    NOT NULL,
    step_index      INTEGER NOT NULL,
    step_description TEXT   NOT NULL,
    tool            TEXT,
    arguments       TEXT    NOT NULL DEFAULT '{}',
    result          TEXT    NOT NULL DEFAULT 'null',
    status          TEXT    NOT NULL,
    elapsed_ms      REAL    NOT NULL DEFAULT 0,
    timestamp       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_run ON agent_audit(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON agent_audit(tenant_id, timestamp);
"""

# ─── Role system prompts ──────────────────────────────────────────────────────

_ROLE_PROMPTS: dict[str, str] = {
    "researcher": (
        "You are a research specialist. Systematically gather information, "
        "cite sources, identify gaps, and present findings clearly."
    ),
    "planner": (
        "You are a strategic planner. Break goals into concrete, ordered steps, "
        "identify dependencies, and anticipate risks."
    ),
    "executor": (
        "You are a precise executor. Follow plans exactly, report results "
        "factually, and escalate when blocked."
    ),
    "verifier": (
        "You are a critical verifier. Check outputs against requirements, "
        "flag inconsistencies, and confirm correctness before marking steps done."
    ),
    "coding": (
        "You are a senior software engineer. Write clean, well-tested code. "
        "Prefer simplicity, document assumptions, and validate inputs."
    ),
    "business": (
        "You are a business analyst. Interpret goals in terms of business value, "
        "ROI, and stakeholder impact. Frame outputs for decision-making."
    ),
    "document": (
        "You are a technical writer. Produce clear, structured documentation. "
        "Use plain language, examples, and consistent formatting."
    ),
    "communication": (
        "You are a communication specialist. Draft messages that are concise, "
        "tone-appropriate, and audience-aware."
    ),
}

# ─── AgentOrchestrator ────────────────────────────────────────────────────────


class AgentOrchestrator:
    """
    Goal-oriented agent orchestrator.

    Args:
        planner: a RulePlanner or LLMPlanner instance (default: RulePlanner).
        llm_engine: object with .generate(prompt, **kwargs)->str for reasoning steps.
        knowledge_base: PersistentKnowledgeBase (or compatible) for RAG context.
        memory_store: SQLiteMemoryStore (or compatible) for conversation memory.
        audit_db_path: path to SQLite file for audit logging (None = no persistence).
        timeout_seconds: wall-clock budget per execute_goal call (0 = unlimited).
    """

    def __init__(
        self,
        planner: RulePlanner | LLMPlanner | None = None,
        llm_engine: Any | None = None,
        knowledge_base: Any | None = None,
        memory_store: Any | None = None,
        audit_db_path: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._planner = planner or RulePlanner()
        self._llm = llm_engine
        self._kb = knowledge_base
        self._mem = memory_store
        self._timeout = timeout_seconds
        self._tools: dict[str, ToolEntry] = {}
        self._audit_conn: sqlite3.Connection | None = None

        if audit_db_path:
            Path(audit_db_path).parent.mkdir(parents=True, exist_ok=True)
            self._audit_conn = sqlite3.connect(audit_db_path, check_same_thread=False)
            self._audit_conn.executescript(_AUDIT_DDL)
            self._audit_conn.commit()

    # ── Tool registry ─────────────────────────────────────────────────────────

    def register_tool(
        self,
        tool: Any,
        risk_level: RiskLevel = "low",
        description: str = "",
    ) -> None:
        """Register a tool instance. The tool must have a .name attribute and .run(**kw) method."""
        name = getattr(tool, "name", None)
        if not name:
            raise ValueError("Tool must have a non-empty .name attribute")
        self._tools[name] = ToolEntry(tool=tool, risk_level=risk_level, description=description)
        logger.debug("Registered tool %r (risk=%s)", name, risk_level)

    def available_tools(self, exclude_risk: set[RiskLevel] | None = None) -> list[str]:
        """Return list of registered tool names, optionally excluding by risk level."""
        if not exclude_risk:
            return list(self._tools)
        return [name for name, e in self._tools.items() if e.risk_level not in exclude_risk]

    # ── Main execution loop ───────────────────────────────────────────────────

    def execute_goal(
        self,
        goal: str,
        tool_args: dict[str, dict] | None = None,
        tenant_id: str = "default",
        user_id: str = "default",
        max_steps: int = 8,
        require_approval_for: set[RiskLevel] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a goal through the full agent loop:
        analyze → plan → execute tools → observe → verify → finish.

        Args:
            goal: natural-language goal.
            tool_args: {tool_name: {extra kwargs}} merged into step arguments.
            tenant_id: tenant scope for memory and RAG.
            user_id: user scope for memory.
            max_steps: hard cap on plan steps.
            require_approval_for: set of risk levels that need human approval
                                   (steps with those risk levels are skipped with an
                                    'approval_required' status and explanation).

        Returns:
            Structured result dict with plan, reflection, and final output.
        """
        run_id = str(uuid.uuid4())
        deadline = time.monotonic() + self._timeout if self._timeout > 0 else float("inf")
        approval_gate = require_approval_for or set()
        provided = tool_args or {}
        audit_log: list[AuditEntry] = []

        # ── 1. Analyze: build context from memory + RAG ───────────────────────
        context_text = ""
        context_citations: list[dict] = []

        if self._kb and hasattr(self._kb, "build_context"):
            try:
                rag_result = self._kb.build_context(goal, tenant_id, k=4)
                context_text = rag_result.get("context_text", "")
                context_citations = rag_result.get("citations", [])
            except Exception as exc:
                logger.warning("RAG context fetch failed: %s", exc)

        memory_snippets: list[str] = []
        if self._mem and hasattr(self._mem, "get_relevant"):
            try:
                mems = self._mem.get_relevant(goal, tenant_id, user_id, limit=6)
                memory_snippets = [m.content for m in mems]
            except Exception as exc:
                logger.warning("Memory fetch failed: %s", exc)

        # ── 2. Plan ───────────────────────────────────────────────────────────
        tools_list = self.available_tools(exclude_risk=None)
        plan: Plan = self._planner.create(goal, tools_list, max_steps=max_steps)

        # ── 3. Execute steps ──────────────────────────────────────────────────
        for step_idx, step in enumerate(plan.steps):
            if time.monotonic() > deadline:
                step.status = StepStatus.skipped
                step.result = {"error": "budget_exceeded"}
                continue

            # Dependency gate: skip if any dependency failed
            if not self._deps_satisfied(plan.steps, step):
                step.status = StepStatus.skipped
                step.result = {"error": "dependency_failed"}
                continue

            step.status = StepStatus.running
            t0 = time.monotonic()

            # Approval gate
            if step.tool:
                entry = self._tools.get(step.tool)
                if entry and entry.risk_level in approval_gate:
                    step.status = StepStatus.skipped
                    step.result = {
                        "approval_required": True,
                        "risk_level": entry.risk_level,
                        "message": (
                            f"Tool {step.tool!r} requires human approval "
                            f"(risk={entry.risk_level})"
                        ),
                    }
                    self._audit(
                        run_id, tenant_id, user_id, goal, step_idx, step,
                        time.monotonic() - t0, audit_log,
                    )
                    continue

            # Tool execution step
            if step.tool:
                step.status, step.result = self._run_tool_step(
                    step, provided.get(step.tool, {}), deadline
                )
            else:
                # Reasoning step — call LLM if available
                step.status, step.result = self._run_reasoning_step(
                    step, goal, context_text, memory_snippets, plan, step_idx
                )

            elapsed = time.monotonic() - t0
            self._audit(run_id, tenant_id, user_id, goal, step_idx, step, elapsed, audit_log)

        # ── 4. Verify / reflect ───────────────────────────────────────────────
        reflection = self._planner.reflect(plan)

        # ── 5. Final synthesis ────────────────────────────────────────────────
        final_output = self._synthesize(goal, plan, context_text, memory_snippets)

        # Persist conversation turn to memory
        if self._mem and hasattr(self._mem, "add"):
            try:
                self._mem.add(
                    tenant_id, user_id,
                    content=f"Goal: {goal}\n\nResult: {final_output[:500]}",
                    kind="episodic",
                    metadata={"run_id": run_id},
                    provenance={"agent": "orchestrator", "run_id": run_id},
                )
            except Exception as exc:
                logger.warning("Memory persist failed: %s", exc)

        self._flush_audit(audit_log)

        return {
            "run_id": run_id,
            "goal": goal,
            "plan": asdict(plan),
            "reflection": reflection,
            "final_output": final_output,
            "context_citations": context_citations,
            "audit_entries": len(audit_log),
        }

    # ── Step execution helpers ────────────────────────────────────────────────

    def _run_tool_step(
        self,
        step: PlanStep,
        extra_args: dict,
        deadline: float,
    ) -> tuple[StepStatus, Any]:
        entry = self._tools.get(step.tool or "")
        if entry is None:
            return StepStatus.failed, {"error": f"tool not registered: {step.tool!r}"}

        args = {**step.arguments, **extra_args}
        last_error: str = ""
        attempts = max(1, step.retries + 1)

        for attempt in range(attempts):
            if time.monotonic() > deadline:
                return StepStatus.failed, {"error": "budget_exceeded"}
            try:
                result = entry.tool.run(**args)
                if result.ok:
                    return StepStatus.done, result.data
                last_error = result.error or "tool returned not-ok"
                logger.warning(
                    "Tool %r attempt %d/%d failed: %s",
                    step.tool, attempt + 1, attempts, last_error,
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Tool %r attempt %d/%d raised: %s",
                    step.tool, attempt + 1, attempts, exc,
                )

        return StepStatus.failed, {"error": last_error}

    def _run_reasoning_step(
        self,
        step: PlanStep,
        goal: str,
        context_text: str,
        memory_snippets: list[str],
        plan: Plan,
        step_idx: int,
    ) -> tuple[StepStatus, Any]:
        if self._llm is None:
            return StepStatus.done, {
                "note": "reasoning step; no llm_engine configured — attach one for real inference"
            }

        completed_summaries = []
        for i, s in enumerate(plan.steps[:step_idx]):
            if s.status == StepStatus.done and s.result:
                completed_summaries.append(f"Step {i+1} ({s.description}): {str(s.result)[:300]}")

        prompt_parts = [f"Goal: {goal}", f"Current step: {step.description}"]
        if context_text:
            prompt_parts.append(f"Relevant context:\n{context_text[:1000]}")
        if memory_snippets:
            prompt_parts.append("Relevant memory:\n" + "\n".join(f"- {m}" for m in memory_snippets[:3]))
        if completed_summaries:
            prompt_parts.append("Steps completed so far:\n" + "\n".join(completed_summaries))
        prompt_parts.append("Please complete this reasoning step concisely.")

        prompt = "\n\n".join(prompt_parts)
        try:
            response = self._llm.generate(prompt)
            return StepStatus.done, {"reasoning": response}
        except Exception as exc:
            logger.warning("LLM reasoning step failed: %s", exc)
            return StepStatus.failed, {"error": str(exc)}

    def _synthesize(
        self,
        goal: str,
        plan: Plan,
        context_text: str,
        memory_snippets: list[str],
    ) -> str:
        if self._llm is None:
            done_results = [
                s.result for s in plan.steps
                if s.status == StepStatus.done and s.result
            ]
            if done_results:
                return f"Completed {len(done_results)} step(s). Last result: {str(done_results[-1])[:400]}"
            return f"Plan executed for goal: {goal}"

        step_summaries = []
        for i, s in enumerate(plan.steps):
            res_str = str(s.result)[:300] if s.result else "no result"
            step_summaries.append(f"Step {i+1} [{s.status}] {s.description}: {res_str}")

        prompt_parts = [
            f"Goal: {goal}",
            "Execution summary:\n" + "\n".join(step_summaries),
        ]
        if context_text:
            prompt_parts.append(f"Knowledge context:\n{context_text[:800]}")
        if memory_snippets:
            prompt_parts.append("Relevant memory:\n" + "\n".join(f"- {m}" for m in memory_snippets[:3]))
        prompt_parts.append(
            "Based on the above, provide a clear, concise final answer or summary for the goal."
        )

        try:
            return self._llm.generate("\n\n".join(prompt_parts))
        except Exception as exc:
            logger.warning("LLM synthesis failed: %s", exc)
            return f"Synthesis failed: {exc}"

    @staticmethod
    def _deps_satisfied(steps: list[PlanStep], step: PlanStep) -> bool:
        for dep_idx in step.depends_on:
            if 0 <= dep_idx < len(steps):
                if steps[dep_idx].status not in (StepStatus.done, StepStatus.skipped):
                    return False
        return True

    # ── Audit ─────────────────────────────────────────────────────────────────

    def _audit(
        self,
        run_id: str,
        tenant_id: str,
        user_id: str,
        goal: str,
        step_idx: int,
        step: PlanStep,
        elapsed: float,
        audit_log: list[AuditEntry],
    ) -> None:
        entry = AuditEntry(
            run_id=run_id,
            tenant_id=tenant_id,
            user_id=user_id,
            goal=goal[:200],
            step_index=step_idx,
            step_description=step.description,
            tool=step.tool,
            arguments=step.arguments,
            result=step.result,
            status=str(step.status),
            elapsed_ms=round(elapsed * 1000, 2),
        )
        audit_log.append(entry)

    def _flush_audit(self, audit_log: list[AuditEntry]) -> None:
        if self._audit_conn is None or not audit_log:
            return
        for e in audit_log:
            try:
                self._audit_conn.execute(
                    """INSERT INTO agent_audit
                       (run_id, tenant_id, user_id, goal, step_index, step_description,
                        tool, arguments, result, status, elapsed_ms, timestamp)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        e.run_id, e.tenant_id, e.user_id, e.goal,
                        e.step_index, e.step_description,
                        e.tool,
                        json.dumps(e.arguments, default=str),
                        json.dumps(e.result, default=str),
                        e.status, e.elapsed_ms, e.timestamp,
                    ),
                )
            except Exception as exc:
                logger.warning("Audit write failed: %s", exc)
        self._audit_conn.commit()

    # ── Role factory ──────────────────────────────────────────────────────────

    @classmethod
    def create_role_agent(
        cls,
        role: str,
        llm_engine: Any | None = None,
        knowledge_base: Any | None = None,
        memory_store: Any | None = None,
        audit_db_path: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> "AgentOrchestrator":
        """
        Factory: create an AgentOrchestrator pre-configured for a specific role.

        Roles: researcher, planner, executor, verifier, coding, business, document, communication.

        The role system prompt is injected into reasoning steps via an LLM engine wrapper
        when an llm_engine is provided.
        """
        if role not in _ROLE_PROMPTS:
            raise ValueError(
                f"Unknown role {role!r}. Available: {sorted(_ROLE_PROMPTS)}"
            )
        system_prompt = _ROLE_PROMPTS[role]
        wrapped_engine = _RoleEngine(llm_engine, system_prompt) if llm_engine else None

        planner: RulePlanner | LLMPlanner
        if wrapped_engine:
            planner = LLMPlanner(
                generate_fn=wrapped_engine.generate,
                fallback=RulePlanner(),
            )
        else:
            planner = RulePlanner()

        return cls(
            planner=planner,
            llm_engine=wrapped_engine,
            knowledge_base=knowledge_base,
            memory_store=memory_store,
            audit_db_path=audit_db_path,
            timeout_seconds=timeout_seconds,
        )


# ─── Role engine wrapper ──────────────────────────────────────────────────────


class _RoleEngine:
    """Wraps an llm_engine and prepends a role system prompt to every generate call."""

    def __init__(self, engine: Any, system_prompt: str) -> None:
        self._engine = engine
        self._system = system_prompt

    def generate(self, prompt: str, **kwargs: Any) -> str:
        full_prompt = f"{self._system}\n\n{prompt}"
        return self._engine.generate(full_prompt, **kwargs)
