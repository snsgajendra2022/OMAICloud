"""Filesystem and execution sandbox constraints."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def discover_repo_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return cur


@dataclass
class SandboxPolicy:
    repo_root: Path = field(default_factory=lambda: discover_repo_root())
    include_user_documents: bool = True
    extra_roots: tuple[Path, ...] = ()

    def allowed_roots(self) -> list[Path]:
        roots = [self.repo_root.resolve()]
        if self.include_user_documents:
            docs = Path.home() / "Documents"
            if docs.is_dir():
                roots.append(docs.resolve())
        roots.extend(p.resolve() for p in self.extra_roots)
        return roots

    def is_path_allowed(self, path: Path | str) -> bool:
        target = Path(path).expanduser().resolve()
        for root in self.allowed_roots():
            try:
                target.relative_to(root)
                return True
            except ValueError:
                continue
        return False
