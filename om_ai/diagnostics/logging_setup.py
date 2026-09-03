"""Application logging bootstrap for OM serve / doctor."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def setup_logging(*, logs_dir: str | Path | None = None, level: int = logging.INFO) -> Path:
    """Configure console + rotating file logs under ``logs/``."""
    root = Path(logs_dir) if logs_dir else (_repo_root() / "logs")
    root.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_handler = RotatingFileHandler(
        root / "application.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setFormatter(fmt)
    app_handler.setLevel(level)

    err_handler = RotatingFileHandler(
        root / "error.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    err_handler.setFormatter(fmt)
    err_handler.setLevel(logging.ERROR)

    sec_handler = RotatingFileHandler(
        root / "security.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    sec_handler.setFormatter(fmt)
    sec_handler.setLevel(level)

    root_logger = logging.getLogger()
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.setLevel(level)
        root_logger.addHandler(app_handler)
        root_logger.addHandler(err_handler)

    sec_logger = logging.getLogger("om_ai.security")
    if not any(isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "").endswith("security.log") for h in sec_logger.handlers):
        sec_logger.addHandler(sec_handler)
        sec_logger.setLevel(level)

    return root
