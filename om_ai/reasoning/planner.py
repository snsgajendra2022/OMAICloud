"""
Planning subsystem: deterministic RulePlanner + LLM-driven LLMPlanner.

RulePlanner — keyword-heuristic baseline (no LLM dependency).
LLMPlanner  — calls a user-supplied generate_fn(prompt)->str to propose a JSON plan;
               falls back to RulePlanner if parsing fails.

Both planners return Plan objects with dependency-aware PlanStep ordering.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ─── Step status ──────────────────────────────────────────────────────────────


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    skipped = "skipped"


# ─── Plan data classes ────────────────────────────────────────────────────────


@dataclass
class PlanStep:
    """
    A single executable step in a plan.

    Attributes:
        description: human-readable intent.
        tool: tool name to invoke (None = reasoning/synthesis step).
        arguments: keyword arguments forwarded to the tool.
        status: current execution status.
        result: output once executed.
        retries: how many retry attempts are allowed.
        depends_on: list of step indices (0-based) that must complete first.
    """

    description: str
    tool: str | None = None
    arguments: dict = field(default_factory=dict)
    status: StepStatus = StepStatus.pending
    result: Any = None
    retries: int = 1
    depends_on: list[int] = field(default_factory=list)


@dataclass
class Plan:
    """Ordered collection of PlanSteps with a goal and unique id."""

    goal: str
    steps: list[PlanStep]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = field(default_factory=dict)


# ─── RulePlanner ─────────────────────────────────────────────────────────────


class RulePlanner:
    """
    Deterministic keyword-heuristic planner.  No LLM required.
    Filters steps to only include tools that are registered as available.
    """

    _TOOL_KEYWORDS: list[tuple[list[str], str]] = [
        (["find", "search", "discover", "lookup", "retrieve"], "knowledge.search"),
        (["api", "endpoint", "openapi", "swagger"],           "discovery.openapi"),
        (["run", "execute", "shell", "command", "script"],    "action.shell"),
        (["project", "scan", "structure", "files"],           "discovery.project"),
    ]

    def create(
        self,
        goal: str,
        available_tools: list[str],
        max_steps: int = 10,
    ) -> Plan:
        lower = goal.lower()
        steps: list[PlanStep] = []
        tool_set = set(available_tools)

        for keywords, tool_name in self._TOOL_KEYWORDS:
            if any(kw in lower for kw in keywords) and tool_name in tool_set:
                steps.append(
                    PlanStep(
                        description=f"Use {tool_name} for: {goal[:80]}",
                        tool=tool_name,
                        arguments={"query": goal} if "search" in tool_name else {},
                        retries=1,
                    )
                )

        steps.append(PlanStep(description="Synthesise available evidence and reasoning"))
        steps.append(PlanStep(description="Produce and verify final response"))

        return Plan(goal=goal, steps=steps[: max_steps])

    def reflect(self, plan: Plan) -> dict:
        """Return a reflection report on plan execution."""
        total = len(plan.steps)
        done = [s for s in plan.steps if s.status == StepStatus.done]
        failed = [s for s in plan.steps if s.status == StepStatus.failed]
        pending = [s for s in plan.steps if s.status == StepStatus.pending]
        complete = (
            total > 0
            and len(failed) == 0
            and len(pending) == 0
            and all(s.status in (StepStatus.done, StepStatus.skipped) for s in plan.steps)
        )
        return {
            "complete": complete,
            "total_steps": total,
            "done": len(done),
            "failed": len(failed),
            "pending": len(pending),
            "failed_steps": [s.description for s in failed],
            "verification_status": "passed" if complete else "incomplete",
        }


# ─── LLMPlanner ──────────────────────────────────────────────────────────────

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    """Extract JSON from a code fence, or return the raw text."""
    m = _JSON_FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


def _parse_plan_steps(
    raw: str,
    available_tools: set[str],
    max_steps: int,
) -> list[PlanStep] | None:
    """
    Parse LLM output into PlanStep list.
    Accepts either:
      {"steps": [...]}
      or a bare array [...]
    Returns None on any parse failure.
    """
    try:
        obj = json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        logger.debug("LLMPlanner JSON parse failed; raw=%r", raw[:200])
        return None

    if isinstance(obj, dict):
        raw_steps = obj.get("steps", [])
    elif isinstance(obj, list):
        raw_steps = obj
    else:
        return None

    if not isinstance(raw_steps, list) or not raw_steps:
        return None

    steps: list[PlanStep] = []
    for i, item in enumerate(raw_steps[:max_steps]):
        if not isinstance(item, dict):
            continue
        tool = item.get("tool") or None
        # Tool permission filter: only include tools the orchestrator has registered
        if tool and tool not in available_tools:
            logger.warning("LLMPlanner proposed unknown tool %r — step will have no tool", tool)
            tool = None
        steps.append(
            PlanStep(
                description=str(item.get("description", f"Step {i + 1}")),
                tool=tool,
                arguments=item.get("arguments", {}),
                retries=int(item.get("retries", 1)),
                depends_on=[int(d) for d in item.get("depends_on", [])],
            )
        )

    return steps if steps else None


class LLMPlanner:
    """
    LLM-driven planner.

    The caller supplies ``generate_fn``, a callable with signature:
        generate_fn(prompt: str, **kwargs) -> str

    The prompt asks the LLM for a JSON plan.  If the response cannot be parsed,
    the planner falls back to RulePlanner silently.

    The JSON schema the LLM should return:
        {
          "steps": [
            {
              "description": "...",
              "tool": "<tool_name or null>",
              "arguments": {},
              "retries": 1,
              "depends_on": []
            },
            ...
          ]
        }
    """

    _SYSTEM_PROMPT = """\
You are a planning assistant. Given a goal and a list of available tools, output a JSON plan.

Available tools: {tools}

Rules:
- Respond ONLY with valid JSON wrapped in a ```json code fence.
- The JSON must be: {{"steps": [...]}}
- Each step: {{"description": str, "tool": str|null, "arguments": {{}}, "retries": 1, "depends_on": []}}
- "tool" must be one of the available tools or null (for reasoning steps).
- "depends_on" lists 0-based indices of steps that must complete before this step runs.
- Maximum {max_steps} steps.
- Do not include explanations outside the JSON fence.
"""

    def __init__(
        self,
        generate_fn: Callable[[str], str],
        fallback: RulePlanner | None = None,
        max_steps: int = 8,
    ) -> None:
        self._generate = generate_fn
        self._fallback = fallback or RulePlanner()
        self._max_steps = max_steps

    def create(
        self,
        goal: str,
        available_tools: list[str],
        max_steps: int | None = None,
    ) -> Plan:
        limit = max_steps or self._max_steps
        tool_set = set(available_tools)

        system = self._SYSTEM_PROMPT.format(
            tools=", ".join(sorted(available_tools)) or "none",
            max_steps=limit,
        )
        prompt = f"{system}\n\nGoal: {goal}"

        try:
            raw = self._generate(prompt)
        except Exception as exc:
            logger.warning("LLMPlanner generate_fn failed (%s); falling back to RulePlanner", exc)
            return self._fallback.create(goal, available_tools, limit)

        steps = _parse_plan_steps(raw, tool_set, limit)
        if steps is None:
            logger.warning("LLMPlanner could not parse LLM output; falling back to RulePlanner")
            return self._fallback.create(goal, available_tools, limit)

        # Topological sort for dependency-aware ordering
        steps = _topo_sort(steps)

        return Plan(goal=goal, steps=steps, metadata={"planner": "llm"})

    def reflect(self, plan: Plan) -> dict:
        return self._fallback.reflect(plan)


# ─── Topological sort ─────────────────────────────────────────────────────────


def _topo_sort(steps: list[PlanStep]) -> list[PlanStep]:
    """
    Return a dependency-respecting ordering of steps using Kahn's algorithm.
    Cycles are broken by ignoring back-edges (graceful degradation).
    """
    n = len(steps)
    in_degree = [0] * n
    adj: list[list[int]] = [[] for _ in range(n)]

    for i, step in enumerate(steps):
        for dep in step.depends_on:
            if 0 <= dep < n and dep != i:
                adj[dep].append(i)
                in_degree[i] += 1

    queue = [i for i in range(n) if in_degree[i] == 0]
    order: list[int] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for nb in adj[node]:
            in_degree[nb] -= 1
            if in_degree[nb] == 0:
                queue.append(nb)

    # If cycle detected, append remaining nodes in original order
    remaining = [i for i in range(n) if i not in set(order)]
    order.extend(remaining)

    return [steps[i] for i in order]
