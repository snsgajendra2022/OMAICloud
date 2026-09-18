"""Process list/start/stop with argv-only subprocess."""
from __future__ import annotations

import os
import platform
import signal
from typing import Any

from om_ai.core.action_control import CommandExecutor


class ProcessController:
    def __init__(self, *, command_executor: CommandExecutor | None = None) -> None:
        self._cmd = command_executor or CommandExecutor()
        self._system = platform.system().lower()

    def list_processes(self, *, limit: int = 50) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        if self._system == "darwin":
            out = self._cmd.run(["ps", "-ax", "-o", "pid=,comm="])
            for line in str(out.get("stdout", "")).splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    rows.append({"pid": int(parts[0]), "name": parts[1]})
        elif self._system == "linux":
            out = self._cmd.run(["ps", "-eo", "pid,comm", "--no-headers"])
            for line in str(out.get("stdout", "")).splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    rows.append({"pid": int(parts[0]), "name": parts[1]})
        else:
            out = self._cmd.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                timeout=30,
            )
            for line in str(out.get("stdout", "")).splitlines():
                if not line.strip():
                    continue
                cols = [c.strip('"') for c in line.split('","')]
                if cols:
                    rows.append({"pid": cols[1] if len(cols) > 1 else "", "name": cols[0]})
        return {"processes": rows[:limit], "count": min(len(rows), limit)}

    def start(self, argv: list[str]) -> dict[str, Any]:
        if isinstance(argv, str):
            raise TypeError("argv must be a list")
        return self._cmd.run([str(x) for x in argv])

    def stop(self, pid: int) -> dict[str, Any]:
        try:
            os.kill(int(pid), signal.SIGTERM)
            return {"pid": pid, "stopped": True}
        except OSError as exc:
            return {"pid": pid, "stopped": False, "error": str(exc)}
