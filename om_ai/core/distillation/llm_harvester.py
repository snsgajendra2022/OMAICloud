"""Call connected teacher LLMs and collect raw responses."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_TEACHERS = ("gpt", "claude", "gemini", "qwen")

TEACHER_SYSTEM = (
    "You are a careful technical teacher. Give a complete, practical answer. "
    "Prefer concrete steps, architecture choices, and trade-offs. "
    "Do not invent fake citations."
)


class LLMHarvester:
    """Harvest answers from external teacher providers (API outputs only)."""

    def __init__(
        self,
        *,
        teachers: list[str] | tuple[str, ...] | None = None,
        chat_fn: Callable[..., tuple[str, str, str]] | None = None,
        stored_keys: dict[str, str] | None = None,
        max_tokens: int = 1200,
        temperature: float = 0.4,
        allow_mock: bool | None = None,
    ) -> None:
        self.teachers = [t.strip().lower() for t in (teachers or DEFAULT_TEACHERS) if t.strip()]
        self.chat_fn = chat_fn
        self.stored_keys = stored_keys or {}
        self.max_tokens = int(max_tokens)
        self.temperature = float(temperature)
        if allow_mock is None:
            allow_mock = os.getenv("OM_DISTILL_ALLOW_MOCK", "1").strip().lower() not in {
                "0",
                "false",
                "no",
                "off",
            }
        self.allow_mock = allow_mock

    def _chat(self) -> Callable[..., tuple[str, str, str]]:
        if self.chat_fn is not None:
            return self.chat_fn
        from om_ai.runtime.external_llms import chat_external

        return chat_external

    def _ready(self, provider_id: str) -> tuple[bool, str]:
        try:
            from om_ai.runtime.external_llms import provider_ready

            return provider_ready(provider_id, stored_keys=self.stored_keys)
        except Exception as exc:
            return False, str(exc)

    def _mock_answer(self, provider_id: str, task: str) -> str:
        """Offline stub — topic-aware (not a generic tenant template)."""
        topic = (task or "topic").strip().splitlines()[0][:160]
        low = topic.lower()
        if provider_id.endswith("weak") or provider_id == "weak":
            return f"Short note on {topic}."

        # Domain packs — keep mocks useful for pipeline tests / offline distill.
        if any(w in low for w in ("react", "jsx", "hooks", "redux", "next.js", "nextjs")):
            bodies = {
                "gpt": (
                    "React is a UI library centered on components, props, and state.\n"
                    "Core building blocks: function components, hooks (useState/useEffect), "
                    "JSX, unidirectional data flow, and composition.\n"
                    "Architecture tips: keep presentational vs container concerns clear, "
                    "colocate state, use context sparingly, prefer server data libraries for fetching."
                ),
                "claude": (
                    "Think in UI trees: each component owns render + local state.\n"
                    "Important patterns: custom hooks, memoization for expensive lists, "
                    "error boundaries, and accessible markup.\n"
                    "Avoid prop drilling with context or a light store; test behavior not implementation."
                ),
                "gemini": (
                    "MVP React architecture: pages → features → shared UI → hooks/services.\n"
                    "Use React Router (or framework routing), a query cache for server state, "
                    "and CSS modules/Tailwind for styling.\n"
                    "Measure re-renders before optimizing."
                ),
                "qwen": (
                    "Step-by-step: 1) define component boundaries 2) lift state only when needed "
                    "3) extract hooks for reusable logic 4) add tests for critical flows "
                    "5) profile and code-split routes.\n"
                    "Trade-off: more abstraction early slows delivery."
                ),
            }
        elif any(w in low for w in ("kubernetes", "k8s", "pod", "cluster", "helm")):
            bodies = {
                "gpt": (
                    "Kubernetes runs containers across nodes with a control plane + workers.\n"
                    "Core objects: Pod, Deployment, Service, Ingress, ConfigMap, Secret.\n"
                    "Plan networking, storage classes, and resource requests/limits early."
                ),
                "claude": (
                    "Separate cluster concerns: control plane health, workload scheduling, "
                    "observability (metrics/logs/traces), and policy (RBAC/network).\n"
                    "Use GitOps for changes; rehearse rollbacks."
                ),
                "gemini": (
                    "Start single-cluster: Deployment + Service + Ingress + HPA.\n"
                    "Add namespaces per team/env; enforce limits; then multi-cluster if needed."
                ),
                "qwen": (
                    "Implementation path: cluster bootstrap → workloads → networking → "
                    "storage → observability → security policies → CI/CD promotion."
                ),
            }
        elif any(w in low for w in ("laravel", "php", "eloquent", "multi tenant", "multitenant", "tenant")):
            bodies = {
                "gpt": (
                    "Laravel multi-tenant design needs clear isolation: DB-per-tenant, "
                    "schema-per-tenant, or shared DB with tenant_id.\n"
                    "Use middleware to resolve tenant, scoped Eloquent queries, "
                    "queues/caches keyed by tenant, and permission gates."
                ),
                "claude": (
                    "Security first: never leak tenant data via global scopes gaps.\n"
                    "Audit auth, file storage paths, and job payloads for tenant context."
                ),
                "gemini": (
                    "MVP: subdomain tenant resolver + tenant_id column + middleware.\n"
                    "Later: move hot tenants to dedicated databases."
                ),
                "qwen": (
                    "Steps: choose tenancy model → middleware → migrations strategy → "
                    "queues/mail → tests for isolation → observability per tenant."
                ),
            }
        elif any(w in low for w in ("python", "django", "fastapi", "flask")):
            bodies = {
                "gpt": (
                    "Structure Python services as API layer → domain services → repositories.\n"
                    "Use typing, tests, and clear dependency injection at boundaries."
                ),
                "claude": (
                    "Prefer explicit interfaces and small modules over deep inheritance.\n"
                    "Document side effects (IO, DB, network) clearly."
                ),
                "gemini": (
                    "Ship a thin FastAPI/Django app first, then extract shared libraries."
                ),
                "qwen": (
                    "Plan: package layout, settings, migrations, auth, background jobs, observability."
                ),
            }
        else:
            bodies = {
                "gpt": (
                    f"For '{topic}', start from requirements, constraints, and success metrics.\n"
                    "Propose a layered design, list trade-offs, and a minimal shippable path."
                ),
                "claude": (
                    f"Explain '{topic}' with assumptions, risks, and failure modes.\n"
                    "Prefer clear steps and verifiable outcomes over buzzwords."
                ),
                "gemini": (
                    f"Practical guide to '{topic}': MVP scope, tools, tests, and iteration loop."
                ),
                "qwen": (
                    f"Break '{topic}' into steps: understand → design → implement → validate → harden."
                ),
            }

        # Map ollama-style names (qwen3:14b) onto flavor keys
        key = provider_id.lower()
        for alias in ("gpt", "claude", "gemini", "qwen", "deepseek", "mistral"):
            if alias in key:
                key = "qwen" if alias in {"deepseek", "mistral"} else alias
                break
        body = bodies.get(key) or bodies.get("gpt") or next(iter(bodies.values()))
        return (
            f"Teacher view ({provider_id}) for: {topic}\n\n"
            f"{body}\n\n"
            "Keep answers concrete; verify against your stack before production use."
        )

    def harvest(self, task: str, *, teachers: list[str] | None = None) -> dict[str, Any]:
        task = (task or "").strip()
        if not task:
            raise ValueError("task is required")
        ids = [t.strip().lower() for t in (teachers or self.teachers) if t.strip()]
        chat = self._chat()
        responses: list[dict[str, Any]] = []
        for pid in ids:
            ok, reason = self._ready(pid)
            entry: dict[str, Any] = {
                "provider": pid,
                "ok": False,
                "text": "",
                "model": "",
                "vendor": "",
                "error": "",
                "source": "live",
            }
            try:
                if not ok:
                    if self.allow_mock:
                        entry["text"] = self._mock_answer(pid, task)
                        entry["ok"] = True
                        entry["model"] = f"{pid}-mock"
                        entry["vendor"] = "mock"
                        entry["source"] = "mock"
                        entry["error"] = f"provider_not_ready:{reason}"
                    else:
                        entry["error"] = reason or "provider_not_ready"
                else:
                    text, display, vendor = chat(
                        pid,
                        [
                            {"role": "system", "content": TEACHER_SYSTEM},
                            {"role": "user", "content": task},
                        ],
                        stored_keys=self.stored_keys,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )
                    entry["text"] = str(text or "").strip()
                    entry["model"] = str(display or pid)
                    entry["vendor"] = str(vendor or pid)
                    entry["ok"] = bool(entry["text"])
                    if not entry["ok"]:
                        entry["error"] = "empty_response"
            except Exception as exc:
                logger.debug("teacher %s failed: %s", pid, exc)
                if self.allow_mock:
                    entry["text"] = self._mock_answer(pid, task)
                    entry["ok"] = True
                    entry["model"] = f"{pid}-mock"
                    entry["vendor"] = "mock"
                    entry["source"] = "mock"
                    entry["error"] = str(exc)
                else:
                    entry["error"] = str(exc)
            responses.append(entry)

        ok_count = sum(1 for r in responses if r.get("ok") and r.get("text"))
        return {
            "task": task,
            "teachers": ids,
            "responses": responses,
            "ok_count": ok_count,
            "live_count": sum(1 for r in responses if r.get("source") == "live" and r.get("ok")),
            "mock_count": sum(1 for r in responses if r.get("source") == "mock" and r.get("ok")),
        }
