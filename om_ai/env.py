"""Load a local ``.env`` file into ``os.environ`` (process startup helper).

Writing keys into ``.env`` alone does nothing until something loads them.
``om-ai serve`` / the API call ``load_dotenv()`` so you do not need to
``source .env`` in every new shell.

Existing environment variables win (are not overwritten).
"""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path | None = None, *, override: bool = False) -> Path | None:
    """Parse KEY=VALUE lines from a ``.env`` file into ``os.environ``.

    Returns the path loaded, or ``None`` if no file was found.
    """
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    else:
        cwd = Path.cwd() / ".env"
        candidates.append(cwd)
        # Also try package-repo root when started from a subdirectory.
        here = Path(__file__).resolve().parent.parent / ".env"
        if here != cwd:
            candidates.append(here)

    env_path = next((p for p in candidates if p.is_file()), None)
    if env_path is None:
        return None

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or any(c.isspace() for c in key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if not override and key in os.environ:
            continue
        os.environ[key] = value
    return env_path
