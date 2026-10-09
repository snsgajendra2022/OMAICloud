#!/usr/bin/env python3
"""Static audit of OM's Python architecture and model-generation paths."""
from __future__ import annotations
import argparse, ast, json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("om_ai", "scripts")
GENERATION_METHODS = {"generate", "chat", "chat_reply", "run_chat_pipeline", "forward", "stream"}
TOKENIZER_TERMS = ("tokenizer", "vocab_size", "tokenize", "decode", "encode")
CHECKPOINT_TERMS = ("checkpoint", "state_dict", "load_state_dict", "torch.load", "safetensors")
ENTRYPOINT_TERMS = ("FastAPI(", "@app.", "@router.", "def main(", "if __name__")


def dotted_name(node: ast.AST) -> str:
    parts = []
    while isinstance(node, (ast.Attribute, ast.Name)):
        parts.append(node.attr if isinstance(node, ast.Attribute) else node.id)
        node = node.value if isinstance(node, ast.Attribute) else None
    return ".".join(reversed(parts))


def module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_local_import(name: str, known: set[str]) -> str | None:
    candidate = name
    while candidate:
        if candidate in known:
            return candidate
        candidate = candidate.rpartition(".")[0]
    return None


def import_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack, on_stack, indices, low, cycles = [], set(), {}, {}, []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for nxt in graph.get(node, set()):
            if nxt not in indices:
                visit(nxt)
                low[node] = min(low[node], low[nxt])
            elif nxt in on_stack:
                low[node] = min(low[node], indices[nxt])
        if low[node] == indices[node]:
            component = []
            while True:
                nxt = stack.pop()
                on_stack.remove(nxt)
                component.append(nxt)
                if nxt == node:
                    break
            if len(component) > 1 or node in graph.get(node, set()):
                cycles.append(sorted(component))

    for node in graph:
        if node not in indices:
            visit(node)
    return sorted(cycles)


def audit() -> dict[str, Any]:
    files = sorted(p for root in SCAN_ROOTS if (ROOT / root).exists()
                   for p in (ROOT / root).rglob("*.py") if "__pycache__" not in p.parts)
    modules = {module_name(p): p for p in files}
    known = set(modules)
    graph: dict[str, set[str]] = defaultdict(set)
    records = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            records.append({"path": str(path.relative_to(ROOT)), "parse_error": str(exc)})
            continue
        imports, functions, calls = set(), [], []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.lower() in GENERATION_METHODS:
                functions.append({"name": node.name, "line": node.lineno, "async": isinstance(node, ast.AsyncFunctionDef)})
            if isinstance(node, ast.Call):
                name = dotted_name(node.func)
                if name and (name.rsplit(".", 1)[-1] in GENERATION_METHODS or ".generate" in name or ".chat" in name):
                    calls.append({"callee": name, "line": node.lineno})
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    package = module_name(path).split(".")[:-1]
                    for _ in range(max(0, node.level - 1)):
                        if package:
                            package.pop()
                    base = ".".join(package + ([base] if base else []))
                if base:
                    imports.add(base)
        local_imports = set()
        for imported in imports:
            local = resolve_local_import(imported, known)
            if local and local != module_name(path):
                local_imports.add(local)
        graph[module_name(path)].update(local_imports)
        lowered = source.lower()
        records.append({
            "path": str(path.relative_to(ROOT)), "module": module_name(path),
            "imports": sorted(imports), "local_imports": sorted(local_imports),
            "generation_functions": sorted(functions, key=lambda x: (x["line"], x["name"])),
            "generation_calls": sorted(calls, key=lambda x: (x["line"], x["callee"])),
            "tokenizer_refs": [x for x in TOKENIZER_TERMS if x in lowered],
            "checkpoint_refs": [x for x in CHECKPOINT_TERMS if x in lowered],
            "entrypoint_markers": [x for x in ENTRYPOINT_TERMS if x in source],
        })
    return {
        "schema_version": 1, "repository_root": str(ROOT), "scan_roots": list(SCAN_ROOTS),
        "file_count": len(files), "parse_errors": [r for r in records if r.get("parse_error")],
        "generation_functions": [{"path": r["path"], **fn} for r in records for fn in r.get("generation_functions", [])],
        "generation_calls": [{"path": r["path"], **call} for r in records for call in r.get("generation_calls", [])],
        "tokenizer_files": [r["path"] for r in records if r.get("tokenizer_refs")],
        "checkpoint_files": [r["path"] for r in records if r.get("checkpoint_refs")],
        "entrypoint_files": [r["path"] for r in records if r.get("entrypoint_markers")],
        "local_import_graph": {k: sorted(v) for k, v in sorted(graph.items())},
        "static_import_cycles": import_cycles(dict(graph)), "files": records,
        "limitations": [
            "Static AST scan cannot discover every dynamic import, plugin, reflection, shell-launched process, or runtime-generated call.",
            "Static import cycles do not prove runtime import failure; runtime smoke tests remain required.",
            "Tokenizer/checkpoint references are lexical signals; runtime bindings require separate verification."
        ]
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OM Architecture Audit (generated)", "",
        f"- Python files scanned: **{report['file_count']}**",
        f"- Static parse errors: **{len(report['parse_errors'])}**",
        f"- Generation-like function definitions: **{len(report['generation_functions'])}**",
        f"- Generation-like call sites: **{len(report['generation_calls'])}**",
        f"- Static import-cycle groups: **{len(report['static_import_cycles'])}**", "",
        "> Static inventory only. It is not a runtime trace and does not establish model quality.", "",
        "## Generation-like function definitions", "",
        "| File | Line | Function | Async |", "|---|---:|---|---|"
    ]
    for item in report["generation_functions"]:
        lines.append(f"| {item['path']} | {item['line']} | {item['name']} | {item['async']} |")
    lines += ["", "## Generation-like call sites", "", "| File | Line | Callee |", "|---|---:|---|"]
    for item in report["generation_calls"]:
        lines.append(f"| {item['path']} | {item['line']} | {item['callee']} |")
    lines += ["", "## Static import cycles", ""]
    lines.extend(["- " + " -> ".join(cycle) for cycle in report["static_import_cycles"]] or ["No local cycles detected by this scan; runtime cycles are not ruled out."])
    lines += ["", "## Parse errors", ""]
    lines.extend([f"- {x['path']}: {x['parse_error']}" for x in report["parse_errors"]] or ["None."])
    for title, key in (("Tokenizer-related files", "tokenizer_files"), ("Checkpoint-related files", "checkpoint_files"), ("API / CLI / runtime entrypoint markers", "entrypoint_files")):
        lines += ["", f"## {title}", ""]
        lines.extend([f"- {p}" for p in report[key]] or ["None detected."])
    lines += ["", "## Limitations", ""]
    lines.extend([f"- {x}" for x in report["limitations"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="artifacts/audit/om_architecture_audit.json")
    parser.add_argument("--markdown", default="docs/OM_ARCHITECTURE_AUDIT.md")
    args = parser.parse_args()
    report = audit()
    json_path, md_path = ROOT / args.json, ROOT / args.markdown
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({
        "file_count": report["file_count"], "parse_errors": len(report["parse_errors"]),
        "generation_functions": len(report["generation_functions"]),
        "generation_calls": len(report["generation_calls"]),
        "static_import_cycles": report["static_import_cycles"],
        "json_report": str(json_path.relative_to(ROOT)),
        "markdown_report": str(md_path.relative_to(ROOT))
    }, indent=2))
    return 1 if report["parse_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
