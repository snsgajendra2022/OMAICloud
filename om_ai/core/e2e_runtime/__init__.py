"""STEPs 36–42 — Chat → E2E integration runtime."""
from __future__ import annotations

from typing import Any

from om_ai.core.chatgpt_runtime import run_chatgpt_runtime
from om_ai.core.continuous_learning import run_continuous_learning
from om_ai.core.enterprise_memory import run_enterprise_memory
from om_ai.core.evaluation_system import run_evaluation_system
from om_ai.core.model_improvement import run_model_improvement
from om_ai.core.production_platform import run_production_platform
from om_ai.core.response.response_intelligence import run_response_intelligence
from om_ai.core.tool_intelligence import run_tool_intelligence
from om_ai.core.agent_runtime import run_agent_runtime
from om_ai.core.chat_intelligence import run_chat_intelligence


def run_step36_chat_core(message: str, **kwargs: Any) -> dict[str, Any]:
    pack = run_chat_intelligence(message, **kwargs)
    pack["step"] = 36
    return pack


def run_step37_response_intelligence(message: str, answer: str = "", **kwargs: Any) -> dict[str, Any]:
    pack = run_response_intelligence(message, answer, **kwargs)
    pack["step"] = 37
    return pack


def run_step38_memory_integration(message: str = "", **kwargs: Any) -> dict[str, Any]:
    mem = run_enterprise_memory(**{k: kwargs[k] for k in ("user_id", "org_id", "project_id") if k in kwargs})
    chat = run_chat_intelligence(message) if message else {}
    return {
        "step": 38,
        "enterprise_memory": mem,
        "conversation_memory": (chat.get("meta") or {}).get("context"),
        "ok": True,
    }


def run_step39_self_evaluation(**kwargs: Any) -> dict[str, Any]:
    pack = run_evaluation_system(**kwargs)
    pack["step"] = 39
    return pack


def run_step40_continuous_learning_loop(message: str = "", answer: str = "") -> dict[str, Any]:
    pack = run_continuous_learning(message, answer, improve=True)
    model = run_model_improvement(gaps=[g.get("gap") for g in ((pack.get("improve") or {}).get("gaps") or []) if isinstance(g, dict)])
    return {"step": 40, "learning": pack, "model_improvement": model}


def run_step41_react_chat_integration(message: str, **kwargs: Any) -> dict[str, Any]:
    """API-shaped payload for React chat UI."""
    pack = run_chatgpt_runtime(message, **kwargs)
    return {
        "step": 41,
        "ok": bool(pack.get("answer")),
        "reply": {
            "role": "assistant",
            "content": pack.get("answer") or "",
        },
        "meta": {
            "stages": pack.get("stages"),
            "source": pack.get("source"),
            "intent": ((pack.get("chat_intelligence") or {}).get("intent")),
            "runtime": "chatgpt_like",
        },
        "raw": pack,
    }


def run_step42_e2e_testing() -> dict[str, Any]:
    cases = [
        "good morning",
        "who are you",
        "My React app has blank page error",
        "what is an API",
        "thanks",
    ]
    rows = []
    for msg in cases:
        out = run_step41_react_chat_integration(msg)
        ans = str((out.get("reply") or {}).get("content") or "")
        rows.append(
            {
                "input": msg,
                "ok": bool(ans.strip()) and "couldn't produce a clear answer" not in ans.lower(),
                "chars": len(ans),
                "preview": ans[:100],
            }
        )
    platform = run_production_platform()
    tools = run_tool_intelligence("search the web for latest react docs")
    agents = run_agent_runtime("plan a coding task")
    evals = run_evaluation_system(limit=2)
    passed = sum(1 for r in rows if r["ok"])
    return {
        "step": 42,
        "chat_cases": rows,
        "chat_pass_rate": round(passed / max(1, len(rows)), 3),
        "platform": platform,
        "tools": {"needs_tools": tools.get("needs_tools"), "tools": tools.get("tools")},
        "agents": {"agents": agents.get("agents"), "stages": agents.get("stages")},
        "evaluation": {"overall": evals.get("overall"), "pass": evals.get("pass")},
        "ok": passed == len(rows),
        "notes": "Chat cases are the hard gate; evaluation suite is advisory seed coverage.",
    }


def run_all_remaining_steps(message: str = "good morning") -> dict[str, Any]:
    return {
        "36": run_step36_chat_core(message),
        "37": run_step37_response_intelligence(message, "hello"),
        "38": run_step38_memory_integration(message),
        "39": run_step39_self_evaluation(limit=2),
        "40": run_step40_continuous_learning_loop(message, "hi"),
        "41": run_step41_react_chat_integration(message),
        "42": run_step42_e2e_testing(),
    }


__all__ = [
    "run_step36_chat_core",
    "run_step37_response_intelligence",
    "run_step38_memory_integration",
    "run_step39_self_evaluation",
    "run_step40_continuous_learning_loop",
    "run_step41_react_chat_integration",
    "run_step42_e2e_testing",
    "run_all_remaining_steps",
]
