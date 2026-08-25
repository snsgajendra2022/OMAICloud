"""Operating Intelligence facade tests."""
from __future__ import annotations

from om_ai.operating_intelligence import capability_status, run_cycle


def test_capability_status_honest():
    st = capability_status()
    assert st["capabilities"]["memory"] == "exists"
    assert st["capabilities"]["electronics_iot"] == "stub"
    assert st["capabilities"]["robotics"] == "stub"


def test_run_cycle_greeting():
    r = run_cycle("hello how are you?", dry_run=True)
    assert r.understood["intent"] == "greeting"
    assert "OM" in r.response
