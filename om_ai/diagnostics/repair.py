"""OM repair helpers — create missing folders / initialize empty DBs."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from om_ai.env import load_dotenv


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _path(key: str, default: str) -> Path:
    raw = (os.getenv(key) or default).strip()
    p = Path(raw)
    if not p.is_absolute():
        p = _repo_root() / p
    return p


def repair_system(*, load_env: bool = True) -> dict[str, Any]:
    """Create standard dirs and touch SQLite databases so serve can start."""
    if load_env:
        load_dotenv()

    root = _repo_root()
    created: list[str] = []
    ensured: list[str] = []

    dirs = [
        root / "artifacts",
        root / "artifacts" / "checkpoints",
        root / "artifacts" / "registry",
        root / "logs",
        root / "storage",
        root / "data" / "om-security",
        root / "data" / "om-memory",
        root / "configs",
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d.relative_to(root)))
        else:
            ensured.append(str(d.relative_to(root)))

    db_specs = [
        ("OM_AI_DB", "artifacts/om_ai.sqlite3"),
        ("OM_AI_KB", "artifacts/knowledge.sqlite3"),
        ("OM_AI_AUDIT_DB", "artifacts/audit.sqlite3"),
        ("OM_AI_TOKENS_DB", "artifacts/tokens.sqlite3"),
        ("OM_AI_ACCOUNTS_DB", "artifacts/accounts.sqlite3"),
        ("OM_AI_FEEDBACK_DB", "artifacts/feedback.sqlite3"),
    ]
    dbs: list[str] = []
    for key, default in db_specs:
        path = _path(key, default)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.execute("SELECT 1")
        conn.close()
        dbs.append(str(path.relative_to(root)) if path.is_relative_to(root) else str(path))

    # Ensure .env exists as a hint file if completely missing (do not overwrite).
    env_path = root / ".env"
    env_note = "present" if env_path.is_file() else "missing (copy from .env.example if available)"

    return {
        "ok": True,
        "created_dirs": created,
        "existing_dirs": ensured,
        "databases": dbs,
        "env": env_note,
        "logs": str((root / "logs").relative_to(root)),
    }
