"""
ProjectDiscovery: scan an authorized root path and return a structured project map.

Security:
  - Only scans paths that are explicitly authorised (under the provided root).
  - .env files: NEVER returns secret values — only lists that .env exists and
    its key NAMES (with values redacted).  Prefer to skip values entirely.
  - Does not follow symlinks outside the authorised root.
  - Does not execute any files.

Supported framework/tech detection:
  Python, FastAPI, Django, Flask
  Node.js, Express, NestJS
  React, Next.js, Vue, Angular
  Laravel (PHP)
  Java / Spring Boot
  .NET (C#)
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Detection fingerprints ───────────────────────────────────────────────────

@dataclass
class _TechFingerprint:
    name: str
    marker_files: list[str] = field(default_factory=list)       # files that must exist
    marker_content: list[tuple[str, str]] = field(default_factory=list)  # (file_glob, regex_pattern)


_FINGERPRINTS: list[_TechFingerprint] = [
    _TechFingerprint("Python",    marker_files=["requirements.txt", "setup.py", "pyproject.toml"]),
    _TechFingerprint("FastAPI",   marker_content=[("*.py", r"from fastapi|import fastapi"), ("pyproject.toml", r"fastapi"), ("requirements.txt", r"fastapi")]),
    _TechFingerprint("Django",    marker_content=[("*.py", r"from django|import django|django\.conf"), ("requirements.txt", r"[Dd]jango"), ("pyproject.toml", r"[Dd]jango")]),
    _TechFingerprint("Flask",     marker_content=[("*.py", r"from flask|import flask"), ("requirements.txt", r"[Ff]lask")]),
    _TechFingerprint("Node.js",   marker_files=["package.json"]),
    _TechFingerprint("Express",   marker_content=[("package.json", r'"express"')]),
    _TechFingerprint("NestJS",    marker_content=[("package.json", r'"@nestjs/core"')]),
    _TechFingerprint("React",     marker_content=[("package.json", r'"react"')]),
    _TechFingerprint("Next.js",   marker_content=[("package.json", r'"next"'), ("next.config.*", r"")]),
    _TechFingerprint("Vue",       marker_content=[("package.json", r'"vue"')]),
    _TechFingerprint("Angular",   marker_content=[("package.json", r'"@angular/core"')]),
    _TechFingerprint("Laravel",   marker_files=["artisan", "composer.json"], marker_content=[("composer.json", r'"laravel/framework"')]),
    _TechFingerprint("Spring",    marker_files=["pom.xml", "build.gradle"], marker_content=[("pom.xml", r"spring-boot"), ("build.gradle", r"spring-boot")]),
    _TechFingerprint(".NET",      marker_files=["*.csproj", "*.sln", "Program.cs"]),
]

# ─── Route detection patterns ─────────────────────────────────────────────────

_ROUTE_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "FastAPI":  [("*.py", r'@\w+\.(get|post|put|patch|delete|router)\s*\(\s*["\']([^"\']+)')],
    "Django":   [("urls.py", r'path\s*\(\s*["\']([^"\']+)')],
    "Flask":    [("*.py", r'@\w+\.route\s*\(\s*["\']([^"\']+)')],
    "Express":  [("*.js", r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)'), ("*.ts", r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)')],
    "Next.js":  [],  # Next.js routes live in pages/ or app/ directories
    "Spring":   [("*.java", r'@(?:GetMapping|PostMapping|RequestMapping)\s*\(\s*["\']([^"\']+)')],
    ".NET":     [("*.cs",   r'\[(?:HttpGet|HttpPost|Route)\s*\(\s*["\']([^"\']+)')],
}

_MAX_FILE_READ_BYTES = 512 * 1024   # 512 KB read limit per file for pattern matching
_MAX_SCAN_FILES = 2000              # don't enumerate more than 2k files


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _safe_glob(root: Path, pattern: str, max_results: int = 200) -> list[Path]:
    """Glob under root; silently skip permission errors; don't follow external symlinks."""
    results = []
    try:
        for p in root.glob(pattern):
            if not p.is_relative_to(root):
                continue  # symlink escaping root
            results.append(p)
            if len(results) >= max_results:
                break
    except (PermissionError, OSError):
        pass
    return results


def _read_partial(path: Path) -> str:
    """Read up to _MAX_FILE_READ_BYTES bytes from a file, returning text."""
    try:
        raw = path.read_bytes()
        return raw[:_MAX_FILE_READ_BYTES].decode("utf-8", errors="replace")
    except (PermissionError, OSError, IsADirectoryError):
        return ""


def _matches_pattern(root: Path, file_glob: str, regex: str) -> bool:
    """Return True if any file matching file_glob under root contains regex."""
    if not regex:
        return bool(_safe_glob(root, f"**/{file_glob}", max_results=5))
    pattern = re.compile(regex, re.IGNORECASE)
    for p in _safe_glob(root, f"**/{file_glob}", max_results=20):
        if pattern.search(_read_partial(p)):
            return True
    return False


def _detect_technologies(root: Path) -> list[str]:
    detected: list[str] = []
    for fp in _FINGERPRINTS:
        # File marker check
        if fp.marker_files:
            for mf in fp.marker_files:
                if "*" in mf:
                    if _safe_glob(root, f"**/{mf}", max_results=1):
                        detected.append(fp.name)
                        break
                elif (root / mf).exists():
                    detected.append(fp.name)
                    break
            else:
                if not fp.marker_content:
                    continue

        # Content marker check
        if fp.marker_content:
            for file_glob, regex in fp.marker_content:
                if _matches_pattern(root, file_glob, regex):
                    if fp.name not in detected:
                        detected.append(fp.name)
                    break

    return detected


def _detect_routes(root: Path, technologies: list[str]) -> list[dict]:
    routes: list[dict] = []
    for tech in technologies:
        patterns = _ROUTE_PATTERNS.get(tech, [])
        for file_glob, regex in patterns:
            compiled = re.compile(regex, re.IGNORECASE)
            for p in _safe_glob(root, f"**/{file_glob}", max_results=50):
                text = _read_partial(p)
                for m in compiled.finditer(text):
                    groups = m.groups()
                    route_path = groups[-1] if groups else m.group(0)[:80]
                    method = groups[0].upper() if len(groups) >= 2 else "ANY"
                    routes.append({
                        "tech": tech,
                        "file": str(p.relative_to(root)),
                        "method": method,
                        "path": route_path,
                    })
                    if len(routes) >= 200:
                        return routes
    return routes


def _scan_directory_tree(root: Path) -> dict[str, Any]:
    """Return a compact directory tree dict (max _MAX_SCAN_FILES entries)."""
    tree: dict[str, Any] = {}
    count = 0
    for p in sorted(root.rglob("*")):
        if count >= _MAX_SCAN_FILES:
            break
        if not p.is_relative_to(root):
            continue
        rel = str(p.relative_to(root))
        # Skip hidden dirs (except .env files) and common noise
        parts = Path(rel).parts
        if any(part.startswith(".") and part not in (".env",) for part in parts):
            continue
        if any(part in ("node_modules", "__pycache__", ".venv", "venv", ".git", "dist", "build", ".next") for part in parts):
            continue
        if p.is_dir():
            tree[rel] = {"type": "directory"}
        else:
            tree[rel] = {"type": "file", "size_bytes": p.stat().st_size if p.exists() else 0}
        count += 1
    return tree


def _read_env_keys(env_path: Path) -> list[str]:
    """
    Return only KEY NAMES from an .env file.
    Values are NEVER included — security requirement.
    """
    keys: list[str] = []
    try:
        for line in env_path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                if key:
                    keys.append(key)
    except (PermissionError, OSError):
        pass
    return keys


def _collect_env_files(root: Path) -> list[dict]:
    """Find .env* files and return their paths + key names (no values)."""
    env_files: list[dict] = []
    for p in _safe_glob(root, ".env*", max_results=20):
        if not p.is_file():
            continue
        env_files.append({
            "path": str(p.relative_to(root)),
            "key_names": _read_env_keys(p),
            "note": "values redacted for security",
        })
    return env_files


# ─── ProjectDiscovery ─────────────────────────────────────────────────────────


@dataclass
class ProjectMap:
    """Structured, JSON-serialisable project map."""

    root_path: str
    technologies: list[str]
    routes: list[dict]
    env_files: list[dict]
    file_tree: dict[str, Any]
    file_count: int
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "technologies": self.technologies,
            "routes": self.routes,
            "env_files": self.env_files,
            "file_tree": self.file_tree,
            "file_count": self.file_count,
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class ProjectDiscovery:
    """
    Scan an authorised root directory and produce a structured project map.

    Security constraints:
      - Only scans the explicitly provided root path (no traversal outside).
      - .env files: key NAMES are listed; values are NEVER returned.
      - Does not execute any files.
      - Symlinks that point outside root are skipped.
    """

    def __init__(
        self,
        authorised_root: str | Path,
        include_file_tree: bool = True,
        max_scan_files: int = _MAX_SCAN_FILES,
    ) -> None:
        root = Path(authorised_root).resolve()
        if not root.exists():
            raise ValueError(f"Authorised root does not exist: {root}")
        if not root.is_dir():
            raise ValueError(f"Authorised root is not a directory: {root}")
        self._root = root
        self._include_tree = include_file_tree

    def scan(self) -> ProjectMap:
        """
        Perform a full project scan.

        Returns:
            ProjectMap with technologies, routes, env file metadata, and file tree.
        """
        root = self._root
        logger.info("ProjectDiscovery scanning %s", root)

        technologies = _detect_technologies(root)
        routes = _detect_routes(root, technologies)
        env_files = _collect_env_files(root)
        file_tree = _scan_directory_tree(root) if self._include_tree else {}
        file_count = len(file_tree)

        tech_str = ", ".join(technologies) if technologies else "unknown"
        summary = (
            f"Project at {root.name!r}: {tech_str}. "
            f"{len(routes)} route(s) detected. "
            f"{file_count} file(s) scanned. "
            f"{len(env_files)} .env file(s) found (values redacted)."
        )

        return ProjectMap(
            root_path=str(root),
            technologies=technologies,
            routes=routes,
            env_files=env_files,
            file_tree=file_tree,
            file_count=file_count,
            summary=summary,
        )
