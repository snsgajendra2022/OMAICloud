"""
SafeShellTool: deny-by-default subprocess execution with strict security controls.

Security model:
  - argv[0] must be in an explicit allowlist (default: echo, pwd, ls).
  - shell=False always (no shell interpolation / injection).
  - Argument path traversal blocked: '..', absolute paths to sensitive dirs,
    and home-dir expansions (~) are rejected.
  - Configurable timeout (default 15 s).
  - Returns structured ToolResult; never raises.
"""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import PurePosixPath
from typing import Any

from .base import Tool, ToolResult

# ─── Blocked path patterns ────────────────────────────────────────────────────

_BLOCKED_PATH_PREFIXES: tuple[str, ...] = (
    "/etc",
    "/var",
    "/root",
    "/proc",
    "/sys",
    "/dev",
    "/boot",
    "/usr/local/etc",
)

_DEFAULT_ALLOWLIST: frozenset[str] = frozenset({"echo", "pwd", "ls"})


def _contains_path_traversal(arg: str) -> bool:
    """Return True if the argument contains a path traversal pattern."""
    # Reject '..' segments (directory traversal)
    parts = PurePosixPath(arg).parts
    if ".." in parts:
        return True
    # Reject home-dir expansion
    if arg.startswith("~"):
        return True
    # Reject absolute paths into sensitive directories
    if arg.startswith("/"):
        for prefix in _BLOCKED_PATH_PREFIXES:
            if arg == prefix or arg.startswith(prefix + "/"):
                return True
    return False


class SafeShellTool(Tool):
    """
    Safe subprocess execution tool.

    Args:
        allowed: explicit set of permitted executable names (argv[0]).
                 Defaults to {'echo', 'pwd', 'ls'}.
        timeout: maximum execution time in seconds (default 15).
        extra_env: additional environment variables merged into the subprocess env.
    """

    name = "action.shell"
    description = (
        "Run an explicitly allow-listed local command without shell interpolation. "
        "Dangerous paths and directory traversal are blocked."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command string to parse and run"},
            "cwd": {"type": "string", "description": "Working directory (optional)"},
        },
        "required": ["command"],
    }
    risk_level = "medium"
    retry = 0

    def __init__(
        self,
        allowed: list[str] | frozenset[str] | None = None,
        timeout: int = 15,
        extra_env: dict[str, str] | None = None,
    ) -> None:
        self._allowed = frozenset(allowed) if allowed is not None else _DEFAULT_ALLOWLIST
        self.timeout = timeout
        self._extra_env = extra_env or {}

    def run(self, command: str = "", cwd: str | None = None, **kwargs: Any) -> ToolResult:
        if not command or not command.strip():
            return ToolResult(False, error="empty command")

        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return ToolResult(False, error=f"command parse error: {exc}")

        if not argv:
            return ToolResult(False, error="empty command after parsing")

        # argv[0] allowlist check
        executable = os.path.basename(argv[0])
        if executable not in self._allowed:
            return ToolResult(
                False,
                error=(
                    f"command not in allowlist: {executable!r}. "
                    f"Allowed: {sorted(self._allowed)}"
                ),
            )

        # Path traversal check on all arguments
        for arg in argv[1:]:
            if _contains_path_traversal(arg):
                return ToolResult(
                    False,
                    error=f"blocked argument with path traversal pattern: {arg!r}",
                )

        # CWD sanity check
        if cwd and _contains_path_traversal(cwd):
            return ToolResult(False, error=f"blocked cwd with path traversal: {cwd!r}")

        # Build clean env
        env = {**os.environ, **self._extra_env}

        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                shell=False,   # NEVER use shell=True
                env=env,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"command timed out after {self.timeout}s")
        except FileNotFoundError:
            return ToolResult(False, error=f"executable not found: {argv[0]!r}")
        except Exception as exc:
            return ToolResult(False, error=str(exc))

        ok = proc.returncode == 0
        data = {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
        return ToolResult(
            ok=ok,
            data=data,
            error=None if ok else f"non-zero exit code: {proc.returncode}",
        )
