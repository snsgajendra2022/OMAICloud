"""OM Autonomous Agent Runtime — STEP 26 production orchestration."""
from __future__ import annotations

import logging
import os
from typing import Any

from .agent_factory import AgentFactory
from .agent_goal import AgentGoal
from .collaboration import AgentCollaboration
from .communication import RuntimeCommunication
from .execution_loop import AgentExecutionLoop
from .planner import AgentPlanner
from .runtime_memory import RuntimeAgentMemory
from .task_queue import AgentTask, AgentTaskQueue

logger = logging.getLogger(__name__)


def _env_on(name: str, default: str = "1") -> bool:
    return (os.getenv(name) or default).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


class OMAutonomousAgentRuntime:
    """
    STEP 26 — Autonomous Agent Runtime Layer.

    Flow:
      create agents → set goals → plan tasks → queue →
      communicate / collaborate → execution loop → memory → pack
    """

    def __init__(self) -> None:
        self.memory = RuntimeAgentMemory()
        self.communication = RuntimeCommunication()
        self.queue = AgentTaskQueue()
        self.factory = AgentFactory()
        self.planner = AgentPlanner()
        self.collaboration = AgentCollaboration(self.communication)
        self.loop = AgentExecutionLoop(
            self.queue, self.memory, self.communication
        )
        self._agents: dict[str, Any] = {}
        self._ready = False
        self._init_error: str | None = None
        self._bootstrap()

    def _bootstrap(self) -> None:
        try:
            self._agents = self.factory.ensure_defaults()
            self._ready = True
        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)
            logger.warning("OMAutonomousAgentRuntime bootstrap failed: %s", exc)

    def status(self) -> dict[str, Any]:
        return {
            "ready": self._ready,
            "step": 26,
            "error": self._init_error,
            "agents": self.factory.list_agents(),
            "queue_size": self.queue.size(),
            "components": {
                "creation": True,
                "memory": True,
                "goals": True,
                "task_queue": True,
                "collaboration": True,
                "communication": True,
                "planning": True,
                "execution_loop": True,
            },
        }

    def create_agent(self, role: str, name: str | None = None) -> Any:
        agent = self.factory.create(role, name=name)
        key = getattr(agent, "name", None) or name or role
        self._agents[str(key)] = agent
        return agent

    def _resolve_agent(self, role: str) -> Any:
        return (
            self._agents.get(role)
            or self.factory.get(role)
            or self.factory.get(f"{role}_agent")
        )

    def _execute_task(self, task: AgentTask, context: dict[str, Any]) -> Any:
        agent = self._resolve_agent(task.agent)
        if agent is None:
            # Lazy-create missing specialty
            agent = self.create_agent(task.agent, name=task.agent)

        payload = {
            **dict(context or {}),
            **dict(task.payload or {}),
            "task_id": task.task_id,
            "goal_id": task.goal_id,
        }

        if hasattr(agent, "execute"):
            try:
                return agent.execute(task.description, context=payload)
            except TypeError:
                return agent.execute(task.description)

        if hasattr(agent, "receive"):
            return agent.receive(task.description)

        return {
            "type": task.agent,
            "task": task.description,
            "analysis": f"{task.agent} acknowledged task",
            "status": "completed",
        }

    def run(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        max_steps: int | None = None,
    ) -> dict[str, Any]:
        """Run the full STEP 26 autonomous agent flow."""
        q = (task or "").strip()
        stages: list[str] = ["agent_runtime"]
        meta: dict[str, Any] = {
            "step": 26,
            "flow": "create→goals→plan→queue→collab→execute→memory→response",
        }
        context = dict(context or {})

        if not q:
            return {
                "answer": "",
                "context_blob": "",
                "stages": stages,
                "meta": {**meta, "empty": True},
                "goal": None,
                "tasks": [],
                "results": [],
                "agents": [],
            }

        if not self._ready:
            return {
                "answer": "",
                "context_blob": "",
                "stages": stages + ["bootstrap_failed"],
                "meta": {**meta, "error": self._init_error},
                "goal": None,
                "tasks": [],
                "results": [],
                "agents": [],
            }

        # 1) Agent creation (ensure specialists exist)
        stages.append("agent_creation")
        try:
            created = self.factory.ensure_defaults()
            self._agents.update(created)
            meta["agent_creation"] = {
                "agents": self.factory.list_agents(),
                "count": len(self.factory.list_agents()),
            }
        except Exception as exc:
            meta["agent_creation"] = {"error": str(exc)}

        # 2) Goals
        stages.append("agent_goals")
        goal: AgentGoal | None = None
        try:
            goal = self.planner.create_goal(q)
            goal.mark("in_progress")
            if goal.owner:
                self.memory.remember_goal(goal.owner, goal.goal_id)
            meta["agent_goals"] = goal.to_dict()
        except Exception as exc:
            meta["agent_goals"] = {"error": str(exc)}

        # 3) Planning
        stages.append("agent_planning")
        plan: dict[str, Any] = {}
        try:
            plan = self.planner.plan(q, context=context)
            if goal is None:
                goal = plan.get("goal")
            meta["agent_planning"] = {
                "roles": list(plan.get("roles") or []),
                "steps": list(plan.get("steps") or []),
                "task_count": len(plan.get("tasks") or []),
            }
        except Exception as exc:
            meta["agent_planning"] = {"error": str(exc)}

        # 4) Task queue
        stages.append("agent_task_queue")
        queued: list[AgentTask] = []
        try:
            self.queue.clear()
            for t in plan.get("tasks") or []:
                self.queue.enqueue(t)
                queued.append(t)
            meta["agent_task_queue"] = {
                "queued": len(queued),
                "agents": [t.agent for t in queued],
            }
        except Exception as exc:
            meta["agent_task_queue"] = {"error": str(exc)}

        # 5) Collaboration kickoff
        stages.append("agent_collaboration")
        collab: dict[str, Any] = {}
        try:
            roles = list(plan.get("roles") or [])
            collab = self.collaboration.collaborate(q, roles, results=[])
            meta["agent_collaboration"] = {
                "team": collab.get("team"),
                "message_count": len(collab.get("messages") or []),
            }
        except Exception as exc:
            meta["agent_collaboration"] = {"error": str(exc)}

        # 6) Communication seed
        stages.append("agent_communication")
        try:
            lead = (collab.get("team") or {}).get("lead") or "orchestrator"
            members = list((collab.get("team") or {}).get("members") or [])
            self.communication.send(
                "orchestrator",
                lead,
                f"Goal {(goal.goal_id if goal else '?')}: {q[:200]}",
                kind="task",
            )
            meta["agent_communication"] = {
                "log_size": len(self.communication.log()),
                "lead": lead,
                "members": members,
            }
        except Exception as exc:
            meta["agent_communication"] = {"error": str(exc)}

        # 7) Execution loop
        stages.append("agent_execution_loop")
        if max_steps is not None:
            self.loop.max_steps = int(max_steps)
        exec_pack: dict[str, Any] = {}
        try:
            exec_pack = self.loop.run(
                executor=lambda t: self._execute_task(t, context)
            )
            meta["agent_execution_loop"] = {
                "steps": exec_pack.get("steps"),
                "ok": exec_pack.get("ok"),
                "pending": exec_pack.get("pending"),
                "errors": list(exec_pack.get("errors") or [])[:5],
            }
        except Exception as exc:
            exec_pack = {"results": [], "steps": 0, "ok": False, "errors": [str(exc)]}
            meta["agent_execution_loop"] = {"error": str(exc)}

        # Finalize collaboration with results
        try:
            flat_results = []
            for item in exec_pack.get("results") or []:
                if isinstance(item, dict) and isinstance(item.get("result"), dict):
                    flat_results.append(item["result"])
                elif isinstance(item, dict):
                    flat_results.append(item)
            collab = self.collaboration.collaborate(
                q, list(plan.get("roles") or []), results=flat_results
            )
        except Exception:
            pass

        if goal is not None:
            goal.mark("done" if exec_pack.get("ok") else "failed")

        # 8) Memory snapshot + response pack
        stages.append("agent_memory")
        memory_snap = self.memory.snapshot()
        meta["agent_memory"] = {
            "episode_count": len(memory_snap.get("episodes") or []),
            "agents_with_memory": list((memory_snap.get("agents") or {}).keys()),
        }

        stages.append("response")
        context_parts: list[str] = []
        if goal is not None:
            context_parts.append(
                f"Agent goal[{goal.goal_id}/{goal.status}]: {goal.description[:240]}"
            )
        if collab.get("summary"):
            context_parts.append(f"Collaboration: {collab.get('summary')}")
        for item in (exec_pack.get("results") or [])[:6]:
            if not isinstance(item, dict):
                continue
            agent = item.get("agent") or "?"
            res = item.get("result")
            analysis = ""
            if isinstance(res, dict):
                analysis = str(
                    res.get("analysis") or res.get("result") or res.get("status") or ""
                )
            elif res is not None:
                analysis = str(res)
            if analysis:
                context_parts.append(f"Agent[{agent}]: {analysis[:400]}")

        context_blob = "\n".join(p for p in context_parts if p).strip()[:6000]
        answer = collab.get("summary") or (
            f"Completed {exec_pack.get('steps', 0)} agent steps for: {q[:160]}"
        )

        return {
            "answer": str(answer),
            "context_blob": context_blob,
            "stages": stages,
            "meta": meta,
            "goal": goal.to_dict() if goal else None,
            "plan": {
                "roles": list(plan.get("roles") or []),
                "steps": list(plan.get("steps") or []),
            },
            "tasks": [t.to_dict() for t in queued],
            "results": list(exec_pack.get("results") or []),
            "collaboration": collab,
            "communication": self.communication.log(30),
            "memory": memory_snap,
            "agents": self.factory.list_agents(),
            "status": self.status(),
        }


_RUNTIME: OMAutonomousAgentRuntime | None = None


def run_agent_runtime(
    task: str,
    *,
    context: dict[str, Any] | None = None,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """Module-level entry used by chat_pipeline / brain_pipeline / STEP stack."""
    global _RUNTIME
    if not _env_on("OM_AGENT_RUNTIME", "1"):
        return {
            "answer": "",
            "context_blob": "",
            "stages": ["agent_runtime_disabled"],
            "meta": {"step": 26, "disabled": True},
            "goal": None,
            "tasks": [],
            "results": [],
            "agents": [],
        }
    if _RUNTIME is None:
        _RUNTIME = OMAutonomousAgentRuntime()
    return _RUNTIME.run(task, context=context, max_steps=max_steps)
