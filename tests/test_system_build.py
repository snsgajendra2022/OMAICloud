"""System build production tests."""
from __future__ import annotations

from pathlib import Path

from om_ai.system import self_check, system_build


def test_system_build_verified(tmp_path: Path):
    (tmp_path / "om_ai").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    cfg = tmp_path / "configs"
    cfg.mkdir()
    for name in ("omai-20m.json", "om-1b.json", "om-7b.json", "om-70b.json"):
        (cfg / name).write_text("{}", encoding="utf-8")
    # Copy minimal package imports still use installed om_ai from site — build uses cwd root for dirs
    report = system_build(tmp_path)
    assert report["mode"] == "PRODUCTION_FOUNDATION_COMPLETE"
    assert report["verified"] is True
    assert (tmp_path / "artifacts" / "SYSTEM_BUILD_REPORT.json").is_file()
