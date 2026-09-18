"""Sandboxed filesystem operations."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from om_ai.core.companion_security import SandboxPolicy


class FileController:
    def __init__(self, sandbox: SandboxPolicy | None = None) -> None:
        self.sandbox = sandbox or SandboxPolicy()

    def _guard(self, path: Path | str) -> Path:
        p = Path(path).expanduser()
        if not self.sandbox.is_path_allowed(p):
            raise PermissionError(f"path not allowed: {p}")
        return p.resolve()

    def list_dir(self, path: str | Path) -> dict[str, Any]:
        root = self._guard(path)
        if not root.is_dir():
            raise FileNotFoundError(str(root))
        entries = sorted(root.iterdir(), key=lambda x: x.name)
        return {
            "path": str(root),
            "entries": [
                {"name": e.name, "is_dir": e.is_dir(), "size": e.stat().st_size}
                for e in entries
            ],
        }

    def read_text(self, path: str | Path, *, encoding: str = "utf-8") -> dict[str, Any]:
        fp = self._guard(path)
        data = fp.read_text(encoding=encoding)
        return {"path": str(fp), "content": data, "bytes": len(data.encode(encoding))}

    def write_text(
        self, path: str | Path, content: str, *, encoding: str = "utf-8"
    ) -> dict[str, Any]:
        fp = self._guard(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding=encoding)
        return {"path": str(fp), "bytes": len(content.encode(encoding))}

    def move(self, src: str | Path, dest: str | Path) -> dict[str, Any]:
        s = self._guard(src)
        d = self._guard(dest)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return {"from": str(s), "to": str(d)}

    def delete(self, path: str | Path) -> dict[str, Any]:
        fp = self._guard(path)
        if fp.is_dir():
            shutil.rmtree(fp)
        elif fp.is_file():
            fp.unlink()
        else:
            raise FileNotFoundError(str(fp))
        return {"deleted": str(fp)}
