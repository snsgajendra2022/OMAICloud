"""Subprocess execution with argv lists only — never shell=True."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Runs trusted argv lists via subprocess with shell=False."""

    def __init__(self, *, default_timeout: float = 120.0) -> None:
        self.default_timeout = default_timeout

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        input_text: str | None = None,
    ) -> dict[str, object]:
        if isinstance(argv, str):
            raise TypeError(
                "argv must be a list of strings; shell strings from model text are forbidden"
            )
        args = [str(a) for a in argv]
        if not args:
            raise ValueError("argv must be non-empty")

        logger.debug("command.exec argv=%r cwd=%s", args, cwd)
        proc = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
            env=dict(env) if env else None,
            timeout=timeout if timeout is not None else self.default_timeout,
            input=input_text,
        )
        return {
            "argv": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
