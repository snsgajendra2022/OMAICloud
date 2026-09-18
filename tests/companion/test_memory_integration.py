"""Companion memory integration tests."""
from pathlib import Path

from om_ai.core.companion_memory.memory_event import MemoryEvent
from om_ai.core.companion_memory.memory_service import MemoryService


def test_remember_and_list(tmp_path: Path):
    path = tmp_path / "memory.json"
    svc = MemoryService(path=str(path))
    evt = svc.remember_turn(
        session_key="s1",
        user_key="u1",
        role="user",
        content="I prefer concise answers",
        intent="preference",
        confidence=0.9,
    )
    assert evt
    svc._save()
    assert path.is_file()
    listed = svc.list_all()
    assert listed is not None


def test_memory_disable_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OM_COMPANION_MEMORY", "0")
    svc = MemoryService(path=str(tmp_path / "m.json"))
    assert svc.disable_memory is True


def test_clear_working(tmp_path: Path):
    svc = MemoryService(path=str(tmp_path / "m2.json"))
    evt = MemoryEvent(kind="working", content="scratch", source="test")
    svc.working.push("s1", evt)
    assert svc.working.items("s1")
    svc.working.clear("s1")
    assert svc.working.items("s1") == []
