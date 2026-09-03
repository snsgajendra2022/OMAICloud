"""OM System Health Check — full stack diagnostics for serve readiness."""
from __future__ import annotations

import importlib
import inspect
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from om_ai.env import load_dotenv


Status = str  # "ok" | "warn" | "fail"


@dataclass
class CheckItem:
    name: str
    status: Status
    detail: str = ""
    path: str = ""

    def mark(self) -> str:
        return {"ok": "✅", "warn": "⚠️", "fail": "❌"}.get(self.status, "?")


@dataclass
class SystemHealthReport:
    items: list[CheckItem] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, status: Status, detail: str = "", path: str = "") -> None:
        self.items.append(CheckItem(name=name, status=status, detail=detail, path=path))

    def by_group(self) -> dict[str, list[CheckItem]]:
        groups: dict[str, list[CheckItem]] = {}
        for item in self.items:
            key = item.name.split(":", 1)[0].strip()
            groups.setdefault(key, []).append(item)
        return groups

    def summary_marks(self) -> dict[str, str]:
        """High-level subsystem marks for the health report."""
        mapping = {
            "Core Brain": "Brain",
            "Memory": "Memory",
            "Knowledge": "Knowledge",
            "Agents": "Agents",
            "Tools": "Tools",
            "Safety": "Safety",
            "Learning": "Learning",
            "Model": "Model",
            "Chat UI": "Chat UI",
            "Startup": "Startup",
            "Database": "Database",
        }
        out: dict[str, str] = {}
        for label, prefix in mapping.items():
            related = [i for i in self.items if i.name.startswith(prefix) or prefix in i.name]
            if not related:
                out[label] = "⚠️"
                continue
            if any(i.status == "fail" for i in related):
                out[label] = "❌"
            elif any(i.status == "warn" for i in related):
                out[label] = "⚠️"
            else:
                out[label] = "✅"
        return out

    def overall(self) -> str:
        if any(i.status == "fail" for i in self.items if i.name.startswith(("Startup", "Brain", "Chat UI"))):
            return "DEGRADED"
        if any(i.status == "fail" for i in self.items):
            return "DEGRADED"
        if any(i.status == "warn" for i in self.items):
            return "READY (WARNINGS)"
        return "READY FOR DEVELOPMENT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall(),
            "summary": self.summary_marks(),
            "checks": [
                {
                    "name": i.name,
                    "status": i.status,
                    "detail": i.detail,
                    "path": i.path,
                    "mark": i.mark(),
                }
                for i in self.items
            ],
            "meta": self.meta,
        }

    def format_report(self) -> str:
        lines = [
            "====================================",
            "     OM SYSTEM HEALTH REPORT",
            "====================================",
            "",
        ]
        for label, mark in self.summary_marks().items():
            lines.append(f"{label:<20}{mark}")
        lines.extend(["", "------------------------------------", "Details:", ""])
        for item in self.items:
            path = f"  ({item.path})" if item.path else ""
            detail = f" — {item.detail}" if item.detail else ""
            lines.append(f"  {item.mark()} {item.name}{detail}{path}")
        lines.extend(
            [
                "",
                f"System: {self.overall()}",
                "====================================",
            ]
        )
        return "\n".join(lines)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env_path(key: str, default: str) -> Path:
    raw = (os.getenv(key) or default).strip()
    p = Path(raw)
    if not p.is_absolute():
        p = _repo_root() / p
    return p


def _check_import(module: str, attr: str | None = None) -> tuple[Status, str, Any]:
    try:
        mod = importlib.import_module(module)
        if attr is None:
            return "ok", f"import {module}", mod
        obj = getattr(mod, attr)
        return "ok", f"{module}.{attr}", obj
    except Exception as exc:
        return "fail", str(exc), None


def _check_db_file(path: Path, *, create_ok: bool = True) -> tuple[Status, str]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            if create_ok:
                conn = sqlite3.connect(str(path))
                conn.execute("SELECT 1")
                conn.close()
                return "warn", f"created empty DB at {path}"
            return "fail", f"missing {path}"
        conn = sqlite3.connect(str(path))
        conn.execute("SELECT 1")
        conn.close()
        return "ok", f"readable {path}"
    except Exception as exc:
        return "fail", str(exc)


def _check_agent_execute(cls: type) -> tuple[Status, str]:
    if not hasattr(cls, "execute"):
        return "fail", "missing execute()"
    try:
        sig = inspect.signature(cls.execute)
        params = list(sig.parameters.keys())
        # expect self, question, context
        if "question" not in params:
            return "fail", f"execute() missing question: {params}"
        if "context" not in params:
            return "warn", f"execute() has no context param: {params}"
        inst = cls()
        out = inst.execute("hello", {})
        if out is None:
            return "warn", "execute() returned None"
        return "ok", f"execute() ok → {type(out).__name__}"
    except Exception as exc:
        return "fail", str(exc)


def run_system_check(*, load_env: bool = True) -> SystemHealthReport:
    """Run full OM stack diagnostics and return a health report."""
    if load_env:
        load_dotenv()

    report = SystemHealthReport()
    root = _repo_root()
    report.meta["repo_root"] = str(root)

    # ------------------------------------------------------------------
    # 1. Application startup
    # ------------------------------------------------------------------
    st, detail, _ = _check_import("fastapi")
    report.add("Startup: FastAPI", st, detail)

    st, detail, _ = _check_import("om_ai.api.main", "app")
    report.add("Startup: FastAPI app", st, detail, "om_ai/api/main.py")

    for router_mod, name in [
        ("om_ai.api.openai_compat", "openai_compat"),
        ("om_ai.api.auth_routes", "auth_routes"),
        ("om_ai.api.conversations", "conversations"),
        ("om_ai.api.workspace_routes", "workspace_routes"),
    ]:
        st, detail, _ = _check_import(router_mod, "router")
        report.add(f"Startup: router {name}", st, detail, router_mod.replace(".", "/") + ".py")

    for html in ("chat.html", "login.html", "register.html", "tokens.html"):
        path = root / "om_ai" / "api" / "static" / html
        report.add(
            f"Chat UI: {html}" if html == "chat.html" else f"Startup: static {html}",
            "ok" if path.is_file() else "fail",
            "found" if path.is_file() else "missing",
            str(path.relative_to(root)),
        )

    required_env = [
        "OM_MODEL_PROVIDER",
        "OM_AI_CHAT_BACKEND",
        "OM_AI_DB",
    ]
    for key in required_env:
        val = os.getenv(key)
        report.add(
            f"Startup: env {key}",
            "ok" if val else "warn",
            val or "unset (defaults may apply)",
        )

    # ------------------------------------------------------------------
    # 2. Databases
    # ------------------------------------------------------------------
    db_keys = [
        ("OM_AI_DB", "artifacts/om_ai.sqlite3"),
        ("OM_AI_KB", "artifacts/knowledge.sqlite3"),
        ("OM_AI_AUDIT_DB", "artifacts/audit.sqlite3"),
        ("OM_AI_TOKENS_DB", "artifacts/tokens.sqlite3"),
        ("OM_AI_ACCOUNTS_DB", "artifacts/accounts.sqlite3"),
        ("OM_AI_FEEDBACK_DB", "artifacts/feedback.sqlite3"),
    ]
    for key, default in db_keys:
        path = _env_path(key, default)
        st, detail = _check_db_file(path)
        report.add(f"Database: {key}", st, detail, str(path))

    # ------------------------------------------------------------------
    # 3. AI Brain
    # ------------------------------------------------------------------
    brain_mods = [
        ("om_ai.core.cognitive.brain_pipeline", "OMCognitiveBrain", "Brain: Cognitive"),
        ("om_ai.core.reasoning.pipeline", "run_reasoning_pipeline", "Brain: Reasoning Pipeline"),
        ("om_ai.cognition.intent_engine", "IntentEngine", "Brain: Intent Engine"),
        ("om_ai.cognition.task_planner", "TaskPlanner", "Brain: Task Planner"),
        ("om_ai.core.response.response_formatter", "ResponseFormatter", "Brain: Response Formatter"),
        ("om_ai.core.reasoning.reasoning_chain", "ReasoningChain", "Brain: Reasoning Chain"),
    ]
    for mod, attr, label in brain_mods:
        st, detail, obj = _check_import(mod, attr)
        report.add(label, st, detail, mod.replace(".", "/") + ".py")
        if st == "ok" and attr == "OMCognitiveBrain" and obj is not None:
            try:
                brain = obj()
                result = brain.process("hello")
                ok = isinstance(result, dict) and ("answer" in result or "user_response" in result)
                report.add(
                    "Brain: process(hello)",
                    "ok" if ok else "warn",
                    "returned keys: " + ", ".join(sorted(result.keys())[:8]) if isinstance(result, dict) else type(result).__name__,
                )
            except Exception as exc:
                report.add("Brain: process(hello)", "fail", str(exc))

    # ------------------------------------------------------------------
    # 4. Agents
    # ------------------------------------------------------------------
    agent_specs = [
        ("om_ai.agents.coding_agent", "CodingAgent"),
        ("om_ai.agents.research_agent", "ResearchAgent"),
        ("om_ai.agents.general_agent", "GeneralAgent"),
    ]
    for mod, cls_name in agent_specs:
        st, detail, cls = _check_import(mod, cls_name)
        if st != "ok" or cls is None:
            report.add(f"Agents: {cls_name}", st, detail, mod.replace(".", "/") + ".py")
            continue
        est, edetail = _check_agent_execute(cls)
        report.add(f"Agents: {cls_name}", est, edetail, mod.replace(".", "/") + ".py")

    st, detail, _ = _check_import("om_ai.agents.router", "AgentRouter")
    report.add("Agents: AgentRouter", st, detail)

    # ------------------------------------------------------------------
    # 5. Tools
    # ------------------------------------------------------------------
    for mod, attr, label in [
        ("om_ai.tools.router", "ToolRouter", "Tools: Tool Router"),
        ("om_ai.tools.security.safety_manager", "ToolSafetyManager", "Tools: Tool Safety"),
        ("om_ai.security.sandbox", "SandboxRunner", "Tools: Execution Sandbox"),
        ("om_ai.actions.shell", "SafeShellTool", "Tools: SafeShellTool"),
    ]:
        st, detail, _ = _check_import(mod, attr)
        report.add(label, st, detail)

    # ------------------------------------------------------------------
    # 6. Memory
    # ------------------------------------------------------------------
    for mod, attr, label in [
        ("om_ai.memory.short_term", "ShortTermMemory", "Memory: Short"),
        ("om_ai.memory.conversation", "ConversationMemory", "Memory: Conversation"),
        ("om_ai.memory.project_memory", "ProjectMemory", "Memory: Project"),
        ("om_ai.memory.long_term", "LongTermMemory", "Memory: Long-term"),
    ]:
        st, detail, _ = _check_import(mod, attr)
        report.add(label, st, detail, mod.replace(".", "/") + ".py")

    # ------------------------------------------------------------------
    # 7. Knowledge
    # ------------------------------------------------------------------
    st, detail, _ = _check_import("om_ai.knowledge", "PersistentKnowledgeBase")
    if st == "fail":
        st, detail, _ = _check_import("om_ai.knowledge.persistent", "PersistentKnowledgeBase")
    report.add("Knowledge: PersistentKnowledgeBase", st, detail)

    # ------------------------------------------------------------------
    # 8. Learning
    # ------------------------------------------------------------------
    for mod, attr, label in [
        ("om_ai.learning.experience", "Experience", "Learning: Experience"),
        ("om_ai.learning.pattern_store", "PatternStore", "Learning: Pattern memory"),
        ("om_ai.learning.learner", "LearningEngine", "Learning: Engine"),
        ("om_ai.self_improvement.engine", "SelfImprovementEngine", "Learning: Self improvement"),
    ]:
        st, detail, _ = _check_import(mod, attr)
        report.add(label, st, detail)

    # ------------------------------------------------------------------
    # 9. Safety
    # ------------------------------------------------------------------
    for mod, attr, label in [
        ("om_ai.safety.risk", "RiskAnalyzer", "Safety: Risk Analyzer"),
        ("om_ai.safety.policy", "PolicyEngine", "Safety: Policy Engine"),
        ("om_ai.safety.permission", "PermissionManager", "Safety: Permission Layer"),
        ("om_ai.security.audit", "AuditLog", "Safety: Audit Logging"),
        ("om_ai.security.policy", "SecurityPolicy", "Safety: Security Policy"),
    ]:
        st, detail, _ = _check_import(mod, attr)
        report.add(label, st, detail)

    # ------------------------------------------------------------------
    # 10. Model checkpoint
    # ------------------------------------------------------------------
    try:
        from om_ai.backends.checkpoint_checker import check_checkpoint

        ck = check_checkpoint()
        model_status = "ok" if ck.get("loading") == "SUCCESS" or ck.get("checkpoint") == "FOUND" else "warn"
        if ck.get("checkpoint") != "FOUND":
            model_status = "warn"
        report.add(
            "Model: Checkpoint",
            model_status,
            f"checkpoint={ck.get('checkpoint')} tokenizer={ck.get('tokenizer')} "
            f"config={ck.get('config')} loading={ck.get('loading')}",
            ck.get("checkpoint_path") or "",
        )
        report.meta["checkpoint"] = ck
    except Exception as exc:
        report.add("Model: Checkpoint", "warn", f"checker error: {exc} (brain-only fallback OK)")

    return report
