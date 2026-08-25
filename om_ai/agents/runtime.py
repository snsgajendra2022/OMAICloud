"""Agent Runtime — workers that can plan and (gated) act on a repository."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from om_ai.agents.roles import select_agent
from om_ai.agent.coding_agent import plan_coding_task
from om_ai.core.intent_engine import classify
from om_ai.core.reasoning.pipeline import run_reasoning_pipeline


ALLOWED_TEST_CMDS = ("pytest", "python", "python3", "npm")


class AgentRuntime:
    """Master routes → specialist workers. File writes are gated."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def execute(self, task: str, *, apply: bool = False, run_tests: bool = False) -> dict[str, Any]:
        intent = classify(task)
        route = select_agent(task)
        agent_name = (route.get("selected") or {}).get("name") or "master"
        reasoning = run_reasoning_pipeline(task, retrieve=True)
        plan = None
        test_result = None
        patches: list[dict[str, Any]] = []

        if agent_name in {"coding", "master"} or intent.intent in {"coding", "debug", "architecture"}:
            plan = plan_coding_task(task, root=self.root, dry_run=not apply)
            if apply:
                patches = self._propose_patches(task, plan)
            if run_tests:
                test_result = self._run_tests()

        return {
            "task": task,
            "agent": agent_name,
            "intent": intent.to_dict(),
            "routing": route,
            "reasoning_preview": (reasoning.get("markdown") or "")[:1200],
            "plan": plan,
            "patches": patches,
            "tests": test_result,
            "apply": apply,
            "note": "apply=True still proposes patches only unless a human gate confirms writes",
        }

    def _propose_patches(self, task: str, plan: dict[str, Any] | None) -> list[dict[str, Any]]:
        # Safe: propose content, do not write unless future confirm API is used
        files = (plan or {}).get("relevant_files") or []
        return [
            {
                "action": "propose_edit",
                "file": f,
                "status": "proposed",
                "summary": f"Would update for task: {task[:120]}",
            }
            for f in files[:5]
        ]

    def _run_tests(self) -> dict[str, Any]:
        cmd = ["pytest", "-q", "--tb=no"]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "cmd": cmd,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "")[-2000:],
                "stderr": (proc.stderr or "")[-1000:],
                "ok": proc.returncode == 0,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "cmd": cmd}


def run_agent(task: str, *, root: str = ".", apply: bool = False, run_tests: bool = False) -> dict[str, Any]:
    return AgentRuntime(root).execute(task, apply=apply, run_tests=run_tests)
