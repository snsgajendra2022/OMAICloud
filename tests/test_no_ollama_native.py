"""Fail if production native paths call Ollama / :11434 without legacy import."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOTS = [
    ROOT / "om_ai" / "api",
    ROOT / "om_ai" / "runtime" / "chat_backend.py",
]

# Concrete client / endpoint signals (calling Ollama, not mentioning the name).
CALL_PATTERNS = [
    re.compile(r"11434"),
    re.compile(r"\bchat_via_ollama\b"),
    re.compile(r"\bollama_base_url\b"),
    re.compile(r"\bollama_reachable\b"),
    re.compile(r"\bollama_model\b"),
    re.compile(r"OM_AI_OLLAMA_"),
    re.compile(r"from\s+om_ai\.legacy\.ollama"),
    re.compile(r"import\s+om_ai\.legacy\.ollama"),
]


def _iter_py_files(path: Path):
    if path.is_file() and path.suffix == ".py":
        yield path
        return
    for p in path.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def _source_has_ollama_calls(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hits: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pat in CALL_PATTERNS:
            if pat.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{i}:{line.strip()}")
                break
    return hits


def test_production_paths_do_not_call_ollama():
    failures: list[str] = []
    for root in PRODUCTION_ROOTS:
        assert root.exists(), f"missing production path: {root}"
        for py in _iter_py_files(root):
            failures.extend(_source_has_ollama_calls(py))
    assert not failures, "Ollama client/endpoint usage in production paths:\n" + "\n".join(
        failures
    )


def test_chat_backend_module_has_no_ollama_client_ast():
    path = ROOT / "om_ai" / "runtime" / "chat_backend.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    assert "chat_via_ollama" not in names
    assert "ollama_reachable" not in names
    assert "ollama_base_url" not in names


def test_configured_backend_rejects_ollama(monkeypatch):
    from om_ai.runtime import chat_backend as cb

    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "ollama")
    monkeypatch.delenv("OM_MODEL_PROVIDER", raising=False)
    with pytest.raises(RuntimeError, match="not part of the OM-1.0 native"):
        cb.configured_backend()


def test_api_main_does_not_import_legacy_ollama():
    text = (ROOT / "om_ai" / "api" / "main.py").read_text(encoding="utf-8")
    assert "om_ai.legacy.ollama" not in text
    assert "11434" not in text


def test_no_11434_in_chat_backend():
    text = (ROOT / "om_ai" / "runtime" / "chat_backend.py").read_text(encoding="utf-8")
    assert "11434" not in text
