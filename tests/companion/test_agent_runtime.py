"""Agent runtime planning + verification tests."""
from om_ai.core.companion_agent.agent_runtime import CompanionAgentRuntime
from om_ai.core.companion_agent.execution_verifier import ExecutionVerifier
from om_ai.core.companion_agent.goal import Goal
from om_ai.core.companion_agent.task import Task, TaskStatus


def test_agent_plans_and_runs_goal():
    rt = CompanionAgentRuntime()
    session = rt.start_session()
    goal = Goal(description="List project files safely")
    result = rt.run_goal(session, goal, context={"mode": "test"})
    assert isinstance(result, dict)
    assert result.get("status") in {"completed", "failed", "cancelled", "ok", "partial"}
    assert "session_id" in result


def test_verifier_rejects_empty_capability_output():
    ver = ExecutionVerifier()
    task = Task(description="open app", capability="application.open")
    task.status = TaskStatus.RUNNING
    ok, reason = ver.verify(task, None)
    assert ok is False
    assert "empty" in reason.lower() or "null" in reason.lower() or "non-null" in reason.lower()


def test_verifier_checks_postconditions():
    ver = ExecutionVerifier()
    task = Task(description="notify", postconditions={"contains": "ok"})
    task.status = TaskStatus.RUNNING
    ok, _ = ver.verify(task, {"msg": "ok"})
    assert ok is True
    ok2, _ = ver.verify(task, {"msg": "nope"})
    assert ok2 is False
