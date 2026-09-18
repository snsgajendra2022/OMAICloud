"""OM Brain Router — STEP 24 production orchestration."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _env_on(name: str, default: str = "1") -> bool:
    return (os.getenv(name) or default).strip().lower() not in {"0", "false", "no", "off"}


class OMBrainRouter:
    """
    One production brain path:

      User
        → Intelligence Fusion (model route)
        → Deep / Autonomous Research (when needed)
        → Knowledge Brain
        → Agents
        → Response pack
    """

    def __init__(self) -> None:
        self._fusion = None
        self._knowledge = None
        self._deep_research = None
        self._auto_research = None
        self._agents = None
        self._agent_impls: dict[str, Any] = {}
        self._ready = False
        self._init_error: str | None = None
        self._bootstrap()

    def _bootstrap(self) -> None:
        try:
            from om_ai.core.intelligence_fusion import (
                IntelligenceEngine,
                IntelligenceModel,
                ModelCapability,
                ModelRegistry,
            )
            from om_ai.core.knowledge_brain import KnowledgeBrain
            from om_ai.core.autonomous_research import AutonomousResearchEngine
            from om_ai.core.autonomous_research.research_goal import ResearchGoal
            from om_ai.core.agents import (
                AgentManager,
                CodingAgent,
                KnowledgeAgent,
                QualityAgent,
                ResearchAgent,
            )
            from om_ai.core.brain_router.deep_research_factory import build_deep_research_engine

            registry = ModelRegistry()
            for model in (
                IntelligenceModel(
                    name="OM-1.0",
                    provider="om_native",
                    capabilities=["chat", "conversation", "general", "coding", "reasoning"],
                    local=True,
                    performance={"latency": "low"},
                ),
                IntelligenceModel(
                    name="OM-Coder",
                    provider="om_native",
                    capabilities=["coding", "architecture", "debug", "software"],
                    local=True,
                ),
                IntelligenceModel(
                    name="OM-Researcher",
                    provider="om_native",
                    capabilities=["research", "analysis", "compare", "latest"],
                    local=True,
                ),
                IntelligenceModel(
                    name="openrouter",
                    provider="openrouter",
                    capabilities=["chat", "reasoning", "research", "coding"],
                    local=False,
                    available=bool(
                        (os.getenv("OPENROUTER_API_KEY") or os.getenv("OM_AI_OPENROUTER_API_KEY") or "").strip()
                    ),
                ),
            ):
                registry.register(model)

            self._fusion = IntelligenceEngine(registry, ModelCapability())
            self._knowledge = KnowledgeBrain()
            self._deep_research = build_deep_research_engine()
            self._auto_research = AutonomousResearchEngine()
            self._ResearchGoal = ResearchGoal
            self._agents = AgentManager()
            self._agent_impls = {
                "coding": CodingAgent(),
                "research": ResearchAgent(),
                "knowledge": KnowledgeAgent(),
                "quality": QualityAgent(),
            }
            self._ready = True
        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)
            logger.warning("OMBrainRouter bootstrap failed: %s", exc)

    def status(self) -> dict[str, Any]:
        return {
            "ready": self._ready,
            "step": 24,
            "error": self._init_error,
            "components": {
                "intelligence_fusion": self._fusion is not None,
                "knowledge_brain": self._knowledge is not None,
                "deep_research": self._deep_research is not None,
                "autonomous_research": self._auto_research is not None,
                "agents": self._agents is not None,
            },
        }

    def run(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        executor: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """Run the full STEP 24 production flow. Always returns a safe pack."""
        q = (message or "").strip()
        stages: list[str] = ["om_brain_router"]
        meta: dict[str, Any] = {
            "step": 24,
            "flow": "intelligence_fusion→research→knowledge→agents→response",
        }
        context = dict(context or {})

        if not q:
            return {
                "answer": "",
                "context_blob": "",
                "stages": stages,
                "meta": {**meta, "empty": True},
                "knowledge_found": False,
                "research_used": False,
                "models": [],
                "agents": [],
            }

        if not self._ready:
            return {
                "answer": "",
                "context_blob": "",
                "stages": stages + ["bootstrap_failed"],
                "meta": {**meta, "error": self._init_error},
                "knowledge_found": False,
                "research_used": False,
                "models": [],
                "agents": [],
            }

        # 1) Intelligence Fusion — pick models for this task
        stages.append("intelligence_fusion")
        models: list[Any] = []
        model_names: list[str] = []
        fusion_out: dict[str, Any] = {}
        try:
            models = list(self._fusion.router.route(q) or [])
            model_names = [getattr(m, "name", str(m)) for m in models]
            meta["intelligence_fusion"] = {
                "routed": model_names,
                "top": model_names[0] if model_names else None,
            }
            if executor is not None and models:
                fusion_out = self._fusion.execute(q, executor=executor) or {}
                meta["intelligence_fusion"]["executed"] = True
        except Exception as exc:
            meta["intelligence_fusion"] = {"error": str(exc)}

        # 2) Research (Deep + Autonomous) when the query needs investigation
        stages.append("research")
        research_pack: dict[str, Any] = {}
        research_used = False
        need_research = any(
            w in q.lower()
            for w in (
                "latest",
                "current",
                "research",
                "compare",
                "architecture",
                "how does",
                "deep dive",
                "analyze",
                "why",
                "what is",
            )
        ) or len(q.split()) >= 6
        if need_research:
            try:
                deep = self._deep_research.research(q)
                if isinstance(deep, dict):
                    research_pack["deep"] = deep
                    research_used = bool(deep.get("research") is not False) or bool(
                        deep.get("evidence")
                    )
            except Exception as exc:
                research_pack["deep_error"] = str(exc)

            try:
                goal = self._ResearchGoal(
                    topic=q[:200], reason="om_brain_router", priority=0.8
                )
                auto = self._auto_research.research(goal)
                if auto:
                    research_pack["autonomous"] = auto
                    research_used = True
            except Exception as exc:
                research_pack["autonomous_error"] = str(exc)
        meta["research"] = {
            "used": research_used,
            "needed": need_research,
            "keys": [k for k in research_pack.keys() if not k.endswith("_error")],
        }

        # 3) Knowledge Brain (after research so findings can enrich concepts)
        stages.append("knowledge_brain")
        knowledge_ctx = None
        knowledge_found = False
        try:
            knowledge_ctx = self._knowledge.analyze(q)
            knowledge_found = bool(getattr(knowledge_ctx, "knowledge_found", False))
            meta["knowledge_brain"] = {
                "knowledge_found": knowledge_found,
                "confidence": float(getattr(knowledge_ctx, "confidence", 0) or 0),
                "concepts": list(getattr(knowledge_ctx, "concepts", []) or []),
            }
            # If knowledge is still thin, force a research pass once.
            if not knowledge_found and not research_used:
                try:
                    deep = self._deep_research.research(q)
                    if isinstance(deep, dict):
                        research_pack["deep"] = deep
                        research_used = bool(deep.get("research") is not False) or bool(
                            deep.get("evidence")
                        )
                        meta["research"]["used"] = research_used
                        meta["research"]["fallback_after_knowledge"] = True
                except Exception as exc:
                    research_pack["deep_error"] = str(exc)
        except Exception as exc:
            meta["knowledge_brain"] = {"error": str(exc)}

        # 4) Agents — STEP 26 Autonomous Agent Runtime
        stages.append("agents")
        agent_route: dict[str, Any] = {}
        agent_results: list[dict[str, Any]] = []
        agent_runtime_pack: dict[str, Any] = {}
        try:
            from om_ai.core.agent_runtime import run_agent_runtime

            agent_runtime_pack = run_agent_runtime(
                q,
                context={
                    **context,
                    "knowledge": knowledge_ctx,
                    "research": research_pack,
                    "models": model_names,
                },
            ) or {}
            agent_results = list(agent_runtime_pack.get("results") or [])
            # Flatten nested execute results for context packing
            flat: list[dict[str, Any]] = []
            for item in agent_results:
                if isinstance(item, dict) and isinstance(item.get("result"), dict):
                    flat.append(
                        {
                            "type": item.get("agent")
                            or item["result"].get("type")
                            or "agent",
                            "analysis": item["result"].get("analysis")
                            or item["result"].get("result")
                            or item["result"].get("validation")
                            or item["result"].get("operation")
                            or item.get("status"),
                            **{
                                k: v
                                for k, v in item["result"].items()
                                if k not in {"analysis"}
                            },
                        }
                    )
                elif isinstance(item, dict):
                    flat.append(item)
            if flat:
                agent_results = flat
            agent_route = {
                "specialty": (agent_runtime_pack.get("plan") or {}).get("roles", ["general"])[
                    0
                ]
                if (agent_runtime_pack.get("plan") or {}).get("roles")
                else "general",
                "team": (agent_runtime_pack.get("collaboration") or {}).get("team"),
                "goal": agent_runtime_pack.get("goal"),
            }
            meta["agents"] = {
                "specialty": agent_route.get("specialty"),
                "ran": [
                    (r.get("type") or r.get("agent"))
                    for r in agent_results
                    if isinstance(r, dict)
                ],
                "team": bool(agent_route.get("team")),
                "step26": True,
                "stages": list(agent_runtime_pack.get("stages") or []),
            }
            meta["step26"] = {
                "goal": agent_runtime_pack.get("goal"),
                "agents": list(agent_runtime_pack.get("agents") or []),
                "ok": bool((agent_runtime_pack.get("status") or {}).get("ready")),
            }
        except Exception as exc:
            # Fallback to lightweight specialty agents
            try:
                agent_route = self._agents.route(q) or {}
                specialty = str(agent_route.get("specialty") or "general")
                wanted = [specialty] if specialty in self._agent_impls else []
                if "quality" not in wanted:
                    wanted.append("quality")
                if research_used and "research" not in wanted:
                    wanted.insert(0, "research")
                if knowledge_found and "knowledge" not in wanted:
                    wanted.insert(0, "knowledge")
                agent_context = {
                    "knowledge": knowledge_ctx,
                    "research": research_pack,
                    "models": model_names,
                }
                for name in wanted:
                    agent = self._agent_impls.get(name)
                    if not agent:
                        continue
                    try:
                        agent_results.append(agent.execute(q, context=agent_context))
                    except Exception as inner:
                        agent_results.append({"type": name, "error": str(inner)})
                meta["agents"] = {
                    "specialty": specialty,
                    "ran": [r.get("type") for r in agent_results if isinstance(r, dict)],
                    "team": bool(agent_route.get("team")),
                    "step26_error": str(exc),
                }
            except Exception as exc2:
                meta["agents"] = {"error": str(exc2), "step26_error": str(exc)}

        # 5) Response pack
        stages.append("response")
        context_parts: list[str] = []
        deep = research_pack.get("deep") if isinstance(research_pack.get("deep"), dict) else {}
        if deep.get("evidence"):
            for ev in list(deep.get("evidence") or [])[:4]:
                claim = getattr(ev, "claim", None) or (
                    ev.get("claim") if isinstance(ev, dict) else None
                )
                if claim:
                    context_parts.append(str(claim)[:500])
            conf = deep.get("confidence")
            if conf is not None:
                context_parts.append(f"Research confidence: {conf}")
        auto = (
            research_pack.get("autonomous")
            if isinstance(research_pack.get("autonomous"), dict)
            else {}
        )
        if auto.get("knowledge"):
            context_parts.append("Autonomous research: " + str(auto.get("knowledge"))[:800])
        if knowledge_found and knowledge_ctx is not None:
            concepts = list(getattr(knowledge_ctx, "concepts", []) or [])
            if concepts:
                context_parts.append(
                    "Knowledge concepts: " + ", ".join(str(c) for c in concepts[:12])
                )
        for ar in agent_results[:3]:
            if isinstance(ar, dict) and ar.get("analysis"):
                context_parts.append(f"Agent[{ar.get('type')}]: {ar.get('analysis')}")
        step26_blob = str((agent_runtime_pack or {}).get("context_blob") or "").strip()
        if step26_blob:
            context_parts.append(step26_blob[:2000])

        context_blob = "\n".join(p for p in context_parts if p).strip()[:6000]

        answer = ""
        if isinstance(fusion_out, dict) and fusion_out.get("answer"):
            answer = str(fusion_out.get("answer") or "").strip()

        return {
            "answer": answer,
            "context_blob": context_blob,
            "stages": stages,
            "meta": meta,
            "knowledge_found": knowledge_found,
            "knowledge": knowledge_ctx,
            "research_used": research_used,
            "research": research_pack,
            "models": model_names,
            "agents": agent_results,
            "agent_route": agent_route,
            "agent_runtime": agent_runtime_pack,
            "fusion": fusion_out,
            "status": self.status(),
        }


_ROUTER: OMBrainRouter | None = None


def run_om_brain_router(
    message: str,
    *,
    context: dict[str, Any] | None = None,
    executor: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Module-level entry used by chat_pipeline / brain_pipeline."""
    global _ROUTER
    if not _env_on("OM_BRAIN_ROUTER", "1"):
        return {
            "answer": "",
            "context_blob": "",
            "stages": ["om_brain_router_disabled"],
            "meta": {"step": 24, "disabled": True},
            "knowledge_found": False,
            "research_used": False,
            "models": [],
            "agents": [],
        }
    if _ROUTER is None:
        _ROUTER = OMBrainRouter()
    return _ROUTER.run(message, context=context, executor=executor)
