"""OM Coding Agent — repository-aware plan / analyze loop.

Capabilities (software):
  - Read repository map
  - Understand rough architecture
  - Propose file changes (dry-run by default)
  - Suggest tests / debug steps
  - Review risks

Does **not** silently rewrite the user's tree unless ``apply=True`` and allow-listed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from om_ai.reasoning.engine import ReasoningEngine


SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "artifacts",
    ".pytest_cache",
    "dist",
    "build",
}


@dataclass
class CodingPlan:
    task: str
    root: str
    architecture: list[str] = field(default_factory=list)
    relevant_files: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    reasoning_md: str = ""
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "root": self.root,
            "architecture": self.architecture,
            "relevant_files": self.relevant_files,
            "steps": self.steps,
            "tests": self.tests,
            "risks": self.risks,
            "dry_run": self.dry_run,
            "reasoning_md": self.reasoning_md,
        }


class CodingAgent:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()
        self.reasoner = ReasoningEngine()

    def map_repo(self, *, max_files: int = 80) -> list[str]:
        files: list[str] = []
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() not in {
                ".py",
                ".ts",
                ".tsx",
                ".js",
                ".jsx",
                ".go",
                ".rs",
                ".java",
                ".md",
                ".json",
                ".toml",
                ".yml",
                ".yaml",
            }:
                continue
            rel = str(p.relative_to(self.root))
            files.append(rel)
            if len(files) >= max_files:
                break
        return files

    def architecture_summary(self, files: list[str]) -> list[str]:
        tops: dict[str, int] = {}
        for f in files:
            top = f.split("/", 1)[0]
            tops[top] = tops.get(top, 0) + 1
        # Prefer package roots over data dumps when present
        boost = {"om_ai": 1000, "tests": 100, "configs": 50, "scripts": 40, "docs": 20}
        ranked = sorted(
            tops.items(),
            key=lambda x: (-(x[1] + boost.get(x[0], 0)), x[0]),
        )[:12]
        return [f"{k}/ ({v} files sampled)" for k, v in ranked]

    def relevant(self, task: str, files: list[str], *, k: int = 15) -> list[str]:
        tokens = {t.lower() for t in task.replace("/", " ").split() if len(t) > 2}
        scored: list[tuple[int, str]] = []
        for f in files:
            fl = f.lower()
            score = sum(1 for t in tokens if t in fl)
            if score:
                scored.append((score, f))
        scored.sort(key=lambda x: (-x[0], x[1]))
        if scored:
            return [f for _, f in scored[:k]]
        return files[: min(k, len(files))]

    def plan(self, task: str, *, dry_run: bool = True) -> CodingPlan:
        files = self.map_repo()
        arch = self.architecture_summary(files)
        rel = self.relevant(task, files)
        trace = self.reasoner.reason(f"Coding task in repo {self.root.name}: {task}")
        steps = [
            "Read relevant files and confirm entrypoints",
            "Write or update a failing test / reproduction",
            "Implement minimal change",
            "Run targeted tests",
            "Review for security / regressions",
            "Summarize diff and deploy notes",
        ]
        tests = [
            "pytest -q (or project test command)",
            "Manual smoke of the changed endpoint/UI path",
        ]
        risks = [
            "Dry-run default: no files modified",
            "Large refactors need human approval",
            "Secrets must never be committed",
        ]
        if not dry_run:
            risks.append("apply=True requested — still requires explicit patch API / human gate")
        return CodingPlan(
            task=task,
            root=str(self.root),
            architecture=arch,
            relevant_files=rel,
            steps=steps,
            tests=tests,
            risks=risks,
            reasoning_md=trace.as_markdown(),
            dry_run=dry_run,
        )


def plan_coding_task(task: str, root: str | Path = ".", *, dry_run: bool = True) -> dict[str, Any]:
    return CodingAgent(root).plan(task, dry_run=dry_run).to_dict()
