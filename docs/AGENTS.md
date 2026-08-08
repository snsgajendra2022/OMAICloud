# Agents

Module: `om_ai/agents/orchestrator.py` — `AgentOrchestrator`.

Planner: `om_ai/reasoning/planner.py` (`RulePlanner`, `LLMPlanner`, plan steps).

Tools: `om_ai/actions/` (`SafeShellTool`, `KnowledgeSearchTool`, base tool protocol).

## Loop

Analyze → plan → execute tools → observe → verify → finish, with per-step retries, wall-clock budget, and optional SQLite audit.

## Features

- Pluggable LLM (`LocalLLMEngine` or any object with `.generate`)
- Optional RAG + memory injection
- Tool registry with risk levels; approval gate for high-risk tools
- Roles: researcher, planner, executor, verifier, coding, business, document, communication
- Tenant/user attribution on audit rows

## Default API wiring

`om_ai/api/main.py` registers:

- allow-listed shell (`OM_AI_ALLOWED_SHELL`)
- knowledge search
- OpenAPI discovery (SSRF-guarded)

## Safety

Deny-by-default shell; never grant broad command execution in production. Agent quality tracks underlying model weights — a tiny checkpoint will plan and tool-call poorly even if the orchestrator is correct.
