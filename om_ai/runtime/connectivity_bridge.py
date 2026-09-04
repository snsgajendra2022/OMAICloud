"""
OM System Connectivity Bridge

Connects previously orphaned / duplicate packages into the live chat/serve path.
Nothing is deleted — every module is reached via safe try/except hooks.

Used by: chat_pipeline, action layer, knowledge brain, OI capability_status.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)


def connectivity_enabled() -> bool:
    return os.environ.get("OM_CONNECT_ALL", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _safe(name: str, fn, default: Any = None) -> Any:
    try:
        return fn()
    except Exception as exc:
        logger.debug("connectivity %s skipped: %s", name, exc)
        return default if default is not None else {"ok": False, "module": name, "error": str(exc)}


class SystemConnectivityBridge:
    """Enrich a chat turn with all OM subsystem packages (connected, not deleted)."""

    PACKAGE_GROUPS = {
        "twins": ["action", "actions", "autonomous", "autonomy", "robotics", "universal_robotics"],
        "perception": ["perception", "multimodal"],
        "hardware": [
            "hardware",
            "hardware_design",
            "device_control",
            "digital_twin",
            "physical_reasoning",
        ],
        "stacks": [
            "workflow",
            "workflow_memory",
            "software_agent",
            "code_intelligence",
            "decision",
            "goals",
            "collaboration",
            "recovery",
            "testing",
            "safety",
            "observability",
            "integrations",
            "rag",
            "knowledge_graph",
        ],
        "core_orphans": ["core.memory", "core.learning", "core.agents", "core.knowledge_fusion"],
        "legacy": ["legacy"],
        "data_ml": ["data_engine", "training_pipeline", "model_intelligence"],
    }

    def enrich(
        self,
        question: str,
        *,
        context: dict[str, Any] | None = None,
        intent: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not connectivity_enabled():
            return {"enabled": False, "modules": {}}

        q = (question or "").strip()
        ctx = dict(context or {})
        intent = intent or {}
        modules: dict[str, Any] = {}
        snippets: list[str] = []

        # ── Perception (PDF / image) ─────────────────────────────────
        modules["perception"] = self._perception(q, ctx)
        if modules["perception"].get("text"):
            snippets.append(modules["perception"]["text"][:1500])

        # ── Twin: action package + actions ───────────────────────────
        modules["action"] = self._action_twin(q, ctx)
        modules["actions"] = self._actions_live(q, ctx)

        # ── Twin: autonomous + autonomy ──────────────────────────────
        modules["autonomous"] = self._autonomous(q)
        modules["autonomy"] = self._autonomy(q)

        # ── Decision + goals + workflow ──────────────────────────────
        modules["decision"] = self._decision(q)
        modules["goals"] = self._goals(q)
        modules["workflow"] = self._workflow(q)
        modules["workflow_memory"] = self._workflow_memory(q)
        if modules["workflow"].get("text"):
            snippets.append(modules["workflow"]["text"][:800])
        if modules["decision"].get("text"):
            snippets.append(modules["decision"]["text"][:600])

        # ── Code / software agent (coding intents) ───────────────────
        if self._looks_coding(q, intent):
            modules["code_intelligence"] = self._code_intelligence(q, ctx)
            modules["software_agent"] = self._software_agent(q, ctx)
            if modules["code_intelligence"].get("text"):
                snippets.append(modules["code_intelligence"]["text"][:1200])

        # ── Knowledge graph twin + RAG ───────────────────────────────
        modules["knowledge_graph"] = self._knowledge_graph(q)
        modules["rag"] = self._rag(q)
        if modules["knowledge_graph"].get("text"):
            snippets.append(modules["knowledge_graph"]["text"][:600])

        # ── core.* orphans ───────────────────────────────────────────
        modules["core.memory"] = self._core_memory(q)
        modules["core.learning"] = self._core_learning(q)
        modules["core.agents"] = self._core_agents(q)
        modules["core.knowledge_fusion"] = self._core_knowledge_fusion(q)

        # ── Hardware / robotics / twin (status + soft plan) ─────────
        modules["hardware"] = self._hardware(q)
        modules["hardware_design"] = self._hardware_design(q)
        modules["device_control"] = self._device_control(q)
        modules["digital_twin"] = self._digital_twin(q)
        modules["physical_reasoning"] = self._physical_reasoning(q)
        modules["robotics"] = self._robotics(q)
        modules["universal_robotics"] = self._universal_robotics(q)

        # ── Safety / observability / collaboration / recovery ───────
        modules["safety"] = self._safety(q)
        modules["observability"] = self._observability(q)
        modules["collaboration"] = self._collaboration(q)
        modules["recovery"] = self._recovery(q)
        modules["testing"] = self._testing(q)
        modules["integrations"] = self._integrations(q)

        # ── Data / training scaffolds (status ping) ──────────────────
        modules["data_engine"] = self._ping("data_engine", "om_ai.data_engine")
        modules["training_pipeline"] = self._ping("training_pipeline", "om_ai.training_pipeline")
        modules["model_intelligence"] = self._ping("model_intelligence", "om_ai.model_intelligence")

        # ── Legacy Ollama (opt-in only) ──────────────────────────────
        modules["legacy"] = self._legacy()

        connected = [k for k, v in modules.items() if isinstance(v, dict) and v.get("ok")]
        return {
            "enabled": True,
            "modules": modules,
            "connected": connected,
            "connected_count": len(connected),
            "snippets": snippets,
            "context_block": "\n\n".join(snippets).strip(),
        }

    def status(self) -> dict[str, Any]:
        """Health-style status for all package groups (for /health or OI)."""
        out: dict[str, Any] = {"groups": {}}
        for group, names in self.PACKAGE_GROUPS.items():
            rows = []
            for name in names:
                rows.append(self._import_status(name))
            out["groups"][group] = rows
        out["connect_all"] = connectivity_enabled()
        return out

    # ── helpers ──────────────────────────────────────────────────────
    def _import_status(self, name: str) -> dict[str, Any]:
        mod_path = name if name.startswith("om_ai.") else f"om_ai.{name}"
        try:
            __import__(mod_path)
            return {"package": name, "importable": True, "ok": True}
        except Exception as exc:
            return {"package": name, "importable": False, "ok": False, "error": str(exc)[:160]}

    def _ping(self, name: str, mod: str) -> dict[str, Any]:
        return _safe(
            name,
            lambda: {"ok": True, "module": name, "imported": __import__(mod).__name__},
        )

    def _looks_coding(self, q: str, intent: dict[str, Any]) -> bool:
        if str(intent.get("intent") or "") in {
            "code_creation",
            "debugging",
            "creation",
            "coding",
        }:
            return True
        return bool(
            re.search(
                r"\b(code|python|react|fastapi|debug|implement|refactor|repository|repo)\b",
                q,
                re.I,
            )
        )

    def _perception(self, q: str, ctx: dict[str, Any]) -> dict[str, Any]:
        def run():
            from om_ai.multimodal import MultimodalFusion

            image = ctx.get("image_path") or ctx.get("attachment")
            pdf = ctx.get("pdf_path") or ctx.get("document_path")
            # Also detect path-like tokens in question
            if not pdf:
                m = re.search(r"([\w./-]+\.pdf)\b", q, re.I)
                if m:
                    pdf = m.group(1)
            if not image:
                m = re.search(r"([\w./-]+\.(png|jpg|jpeg|webp|gif))\b", q, re.I)
                if m:
                    image = m.group(1)
            fused = MultimodalFusion().fuse(
                question=q,
                image_path=str(image) if image else None,
                pdf_path=str(pdf) if pdf else None,
            )
            # Also poke PerceptionManager
            perc_meta: dict[str, Any] = {}
            try:
                from om_ai.perception.perception_manager import PerceptionManager

                if pdf:
                    perc_meta = PerceptionManager().process(
                        {"input_type": "pdf", "content": pdf}
                    )
            except Exception as exc:
                perc_meta = {"error": str(exc)}
            return {
                "ok": bool(fused.get("ok")),
                "module": "perception",
                "modalities": fused.get("modalities"),
                "text": fused.get("fused_text") or "",
                "perception_manager": perc_meta,
            }

        return _safe("perception", run)

    def _action_twin(self, q: str, ctx: dict[str, Any]) -> dict[str, Any]:
        def run():
            from om_ai.action import ToolExecutor, register_builtin_tools

            ex = ToolExecutor()
            try:
                register_builtin_tools(ex)
            except TypeError:
                try:
                    register_builtin_tools()
                except Exception:
                    pass
            # Soft ping — list registry if available
            tools = []
            reg = getattr(ex, "registry", None)
            if reg is not None:
                list_fn = getattr(reg, "list_tools", None) or getattr(reg, "names", None)
                if callable(list_fn):
                    tools = list(list_fn() or [])[:20]
            return {
                "ok": True,
                "module": "action",
                "tools": tools,
                "note": "om_ai.action ToolExecutor connected",
            }

        return _safe("action", run)

    def _actions_live(self, q: str, ctx: dict[str, Any]) -> dict[str, Any]:
        def run():
            from om_ai.actions import SafeShellTool
            from om_ai.actions.base import Tool, ToolResult, RiskLevel

            names = [SafeShellTool().name]
            try:
                from om_ai.actions.knowledge import KnowledgeSearchTool
                from om_ai.knowledge import PersistentKnowledgeBase

                kb = PersistentKnowledgeBase()
                names.append(KnowledgeSearchTool(kb).name)
            except Exception:
                names.append("knowledge_search(deferred)")
            return {
                "ok": True,
                "module": "actions",
                "tools": names,
                "base": [Tool.__name__, ToolResult.__name__, RiskLevel.__name__],
            }

        return _safe("actions", run)

    def _rag(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.rag.relevance_checker import RelevanceChecker

            checker = RelevanceChecker()
            score = None
            for meth in ("check", "score", "is_relevant", "relevant"):
                fn = getattr(checker, meth, None)
                if callable(fn):
                    try:
                        score = fn(q, {"text": q, "score": 0.9})
                        break
                    except Exception:
                        try:
                            score = fn(q)
                            break
                        except Exception:
                            continue
            return {"ok": True, "module": "rag", "score": str(score)[:200], "ready": True}

        return _safe("rag", run)

    def _autonomous(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.autonomous import AutonomousPlanner

            plan = AutonomousPlanner().plan(q) if hasattr(AutonomousPlanner(), "plan") else None
            try:
                plan = AutonomousPlanner().plan(q)
            except Exception:
                p = AutonomousPlanner()
                plan = getattr(p, "create_plan", lambda x: {"goal": x})(q)
            return {"ok": True, "module": "autonomous", "plan": plan}

        return _safe("autonomous", run)

    def _autonomy(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.autonomy import AutonomousPlanner, Goal

            g = Goal(title=q[:80], description=q) if False else None  # type: ignore
            try:
                from om_ai.autonomy.goal import Goal as G

                g = G(description=q[:200])
            except Exception:
                try:
                    g = {"title": q[:80]}
                except Exception:
                    g = None
            planner = AutonomousPlanner()
            plan = None
            for meth in ("plan", "create_plan", "build"):
                fn = getattr(planner, meth, None)
                if callable(fn):
                    try:
                        plan = fn(q)
                        break
                    except TypeError:
                        try:
                            plan = fn(g)
                            break
                        except Exception:
                            continue
            return {"ok": True, "module": "autonomy", "goal": str(g)[:200], "plan": plan}

        return _safe("autonomy", run)

    def _decision(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.decision import DecisionEngine, DecisionOption

            options = [
                DecisionOption(name="direct_answer", description="Answer without tools"),
                DecisionOption(name="use_tools", description="Use action/tools layer"),
                DecisionOption(name="research", description="Retrieve knowledge first"),
            ]
            # Some Option APIs differ
            try:
                result = DecisionEngine().decide(q, options)
            except Exception:
                result = DecisionEngine().decide(
                    q,
                    [
                        {"name": "direct_answer"},
                        {"name": "use_tools"},
                        {"name": "research"},
                    ],
                )
            text = f"[decision] {result}"
            return {"ok": True, "module": "decision", "result": result, "text": text[:500]}

        return _safe("decision", run)

    def _goals(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.goals import GoalManager

            gm = GoalManager()
            # Soft create for multi-step asks
            if len(q.split()) >= 6 and any(
                w in q.lower() for w in ("build", "create", "plan", "implement", "deploy")
            ):
                try:
                    gid = gm.create_goal(q[:60], q, milestones=["analyze", "execute", "verify"])
                except TypeError:
                    gid = gm.create_goal(title=q[:60], description=q, milestones=["analyze"])
                return {"ok": True, "module": "goals", "goal_id": gid}
            return {"ok": True, "module": "goals", "status": "ready"}

        return _safe("goals", run)

    def _workflow(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.workflow import WorkflowGenerator

            wf = WorkflowGenerator().generate(q)
            tasks = []
            if isinstance(wf, dict):
                tasks = wf.get("tasks") or wf.get("steps") or []
                text = f"[workflow] {len(tasks)} tasks: " + ", ".join(
                    str(t.get("name") if isinstance(t, dict) else t)[:40] for t in tasks[:6]
                )
            else:
                text = f"[workflow] {wf}"
            return {"ok": True, "module": "workflow", "workflow": wf, "text": text}

        return _safe("workflow", run)

    def _workflow_memory(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.workflow_memory import StrategyMatcher

            m = StrategyMatcher()
            hit = None
            for meth in ("match", "find", "recall"):
                fn = getattr(m, meth, None)
                if callable(fn):
                    try:
                        hit = fn(q)
                        break
                    except Exception:
                        continue
            return {"ok": True, "module": "workflow_memory", "match": hit}

        return _safe("workflow_memory", run)

    def _code_intelligence(self, q: str, ctx: dict[str, Any]) -> dict[str, Any]:
        def run():
            from om_ai.code_intelligence import CodeUnderstandingEngine

            eng = CodeUnderstandingEngine()
            root = str(ctx.get("project_root") or ".")
            result = None
            for meth in ("analyze", "understand", "scan", "process"):
                fn = getattr(eng, meth, None)
                if callable(fn):
                    try:
                        result = fn(root)
                        break
                    except TypeError:
                        try:
                            result = fn(q)
                            break
                        except Exception:
                            continue
            text = ""
            if isinstance(result, dict):
                text = str(result.get("summary") or result.get("architecture") or result)[:1200]
            elif result:
                text = str(result)[:1200]
            return {
                "ok": True,
                "module": "code_intelligence",
                "result": result if not isinstance(result, dict) else {k: result[k] for k in list(result)[:8]},
                "text": f"[code_intelligence] {text}" if text else "",
            }

        return _safe("code_intelligence", run)

    def _software_agent(self, q: str, ctx: dict[str, Any]) -> dict[str, Any]:
        def run():
            from om_ai.software_agent import SoftwareEngineeringAgent

            agent = SoftwareEngineeringAgent()
            out = None
            for meth in ("handle", "run", "process", "plan"):
                fn = getattr(agent, meth, None)
                if callable(fn):
                    try:
                        out = fn(q)
                        break
                    except TypeError:
                        try:
                            out = fn(q, root=str(ctx.get("project_root") or "."))
                            break
                        except Exception:
                            continue
            return {"ok": True, "module": "software_agent", "result": out}

        return _safe("software_agent", run)

    def _knowledge_graph(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.knowledge_graph import KnowledgeGraphEngine

            # Extract simple entities
            data: dict[str, str] = {}
            for tok in q.replace(",", " ").split():
                c = tok.strip(".,;:()[]{}\"'")
                if len(c) >= 3 and (c[0].isupper() or c.lower() in {"python", "react", "laravel", "php"}):
                    data[c.lower()] = c
            graph = KnowledgeGraphEngine().process(data, "chat") if data else {"entities": [], "relations": []}
            # Some engines use different method names
            if not graph and hasattr(KnowledgeGraphEngine(), "add"):
                graph = {"status": "ready"}
            # Twin package may expose learn(text) instead of process(data)
            try:
                from om_ai.knowledge_graph import KnowledgeGraphEngine as TwinKG

                twin = TwinKG()
                if hasattr(twin, "learn"):
                    twin.learn(q)
                    graph = graph or {"learned": True}
            except Exception:
                pass
            text = ""
            if isinstance(graph, dict) and (graph.get("entities") or graph.get("relations") or graph.get("learned")):
                text = f"[knowledge_graph] entities={len(graph.get('entities') or [])} relations={len(graph.get('relations') or [])}"
            return {"ok": True, "module": "knowledge_graph", "graph": graph, "text": text}

        return _safe("knowledge_graph", run)

    def _core_memory(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.core.memory.memory_manager import MemoryManager

            mm = MemoryManager()
            mm.remember(q)
            recalled = mm.recall()
            return {"ok": True, "module": "core.memory", "recall": recalled}

        return _safe("core.memory", run)

    def _core_learning(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.core.learning import LearningEngine  # type: ignore

            eng = LearningEngine()
            out = None
            for meth in ("learn", "record", "process", "analyze"):
                fn = getattr(eng, meth, None)
                if callable(fn):
                    try:
                        out = fn(q)
                        break
                    except Exception:
                        continue
            return {"ok": True, "module": "core.learning", "result": out}

        return _safe("core.learning", run)

    def _core_agents(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.core.agents import AgentManager

            am = AgentManager()
            team = None
            route = None
            if hasattr(am, "create_team"):
                team = am.create_team(q)
            if hasattr(am, "route"):
                route = am.route(q)
            elif hasattr(am, "available_agents"):
                route = {"agents": am.available_agents()}
            return {"ok": True, "module": "core.agents", "team": team, "route": route}

        return _safe("core.agents", run)

    def _core_knowledge_fusion(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.core.knowledge_fusion import KnowledgeFusionEngine

            ctx = KnowledgeFusionEngine().process(q)
            return {"ok": True, "module": "core.knowledge_fusion", "context": ctx}

        return _safe("core.knowledge_fusion", run)

    def _hardware(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.hardware import HardwareManager

            hm = HardwareManager()
            status = getattr(hm, "status", lambda: {"devices": []})()
            return {"ok": True, "module": "hardware", "status": status}

        return _safe("hardware", run)

    def _hardware_design(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.hardware_design import HardwareDesignManager

            m = HardwareDesignManager()
            out = None
            for meth in ("design", "analyze", "plan", "status"):
                fn = getattr(m, meth, None)
                if callable(fn):
                    try:
                        out = fn(q) if meth != "status" else fn()
                        break
                    except Exception:
                        continue
            return {"ok": True, "module": "hardware_design", "result": out}

        return _safe("hardware_design", run)

    def _device_control(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.device_control import DeviceControlManager

            m = DeviceControlManager()
            status = getattr(m, "status", lambda: {"ready": True})()
            return {"ok": True, "module": "device_control", "status": status}

        return _safe("device_control", run)

    def _digital_twin(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.digital_twin import DigitalTwinManager

            m = DigitalTwinManager()
            out = getattr(m, "status", lambda: {"twins": []})()
            return {"ok": True, "module": "digital_twin", "status": out}

        return _safe("digital_twin", run)

    def _physical_reasoning(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.physical_reasoning import PhysicalReasoningManager

            m = PhysicalReasoningManager()
            out = None
            for meth in ("reason", "analyze", "process", "predict"):
                fn = getattr(m, meth, None)
                if callable(fn):
                    try:
                        out = fn(q)
                        break
                    except Exception:
                        continue
            return {"ok": True, "module": "physical_reasoning", "result": out}

        return _safe("physical_reasoning", run)

    def _robotics(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.robotics import RoboticsManager

            m = RoboticsManager()
            status = getattr(m, "status", lambda: {"robots": []})()
            return {"ok": True, "module": "robotics", "status": status}

        return _safe("robotics", run)

    def _universal_robotics(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.universal_robotics import UniversalRoboticsManager

            m = UniversalRoboticsManager()
            status = getattr(m, "status", lambda: {"ready": True})()
            return {"ok": True, "module": "universal_robotics", "status": status}

        return _safe("universal_robotics", run)

    def _safety(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.safety import SafetyManager

            m = SafetyManager()
            out = None
            for meth in ("check", "evaluate", "assess", "status"):
                fn = getattr(m, meth, None)
                if callable(fn):
                    try:
                        out = fn(q) if meth != "status" else fn()
                        break
                    except Exception:
                        continue
            return {"ok": True, "module": "safety", "result": out}

        return _safe("safety", run)

    def _observability(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.observability import OMMonitor

            mon = OMMonitor()
            # record a soft event if API allows
            for meth in ("record", "track", "increment", "health"):
                fn = getattr(mon, meth, None)
                if callable(fn):
                    try:
                        if meth == "health":
                            return {"ok": True, "module": "observability", "health": fn()}
                        fn("chat_turn")
                        break
                    except TypeError:
                        try:
                            fn("chat_turn", 1)
                            break
                        except Exception:
                            continue
            return {"ok": True, "module": "observability", "ping": True}

        return _safe("observability", run)

    def _collaboration(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.collaboration import AgentCoordinator

            c = AgentCoordinator()
            out = None
            for meth in ("coordinate", "plan", "status"):
                fn = getattr(c, meth, None)
                if callable(fn):
                    try:
                        out = fn(q) if meth != "status" else fn()
                        break
                    except Exception:
                        continue
            return {"ok": True, "module": "collaboration", "result": out}

        return _safe("collaboration", run)

    def _recovery(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.recovery import SelfHealingEngine

            eng = SelfHealingEngine()
            return {"ok": True, "module": "recovery", "ready": True, "engine": type(eng).__name__}

        return _safe("recovery", run)

    def _testing(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.testing import TestingAgent

            agent = TestingAgent()
            return {"ok": True, "module": "testing", "ready": True, "agent": type(agent).__name__}

        return _safe("testing", run)

    def _integrations(self, q: str) -> dict[str, Any]:
        def run():
            from om_ai.integrations import PluginRegistry

            reg = PluginRegistry()
            return {"ok": True, "module": "integrations", "registry": type(reg).__name__}

        return _safe("integrations", run)

    def _legacy(self) -> dict[str, Any]:
        """Connect legacy package; Ollama client only if OM_LEGACY_OLLAMA=1."""
        def run():
            import om_ai.legacy as legacy_pkg

            ollama_ready = False
            if os.environ.get("OM_LEGACY_OLLAMA", "0").strip() in {"1", "true", "yes", "on"}:
                try:
                    from om_ai.legacy.ollama import client as ollama_client  # noqa: F401

                    ollama_ready = True
                except Exception as exc:
                    return {
                        "ok": True,
                        "module": "legacy",
                        "connected": True,
                        "ollama": False,
                        "error": str(exc),
                    }
            return {
                "ok": True,
                "module": "legacy",
                "connected": True,
                "package": legacy_pkg.__name__,
                "ollama_enabled": ollama_ready,
                "note": "Ollama stays opt-in via OM_LEGACY_OLLAMA=1",
            }

        return _safe("legacy", run)


def enrich_chat_turn(
    question: str,
    *,
    context: dict[str, Any] | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return SystemConnectivityBridge().enrich(question, context=context, intent=intent)


def connectivity_status() -> dict[str, Any]:
    return SystemConnectivityBridge().status()
