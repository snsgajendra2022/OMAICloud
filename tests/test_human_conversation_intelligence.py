"""STEP — Real-time Human Conversation Intelligence integration."""
from __future__ import annotations

from om_ai.core.human_conversation_intelligence import get_human_conversation_intelligence
from om_ai.core.speech_intelligence import SentenceCompletion, MeaningReconstruction
from om_ai.core.conversation_timing import get_timing_engine
from om_ai.core.emotional_intelligence import get_emotional_intelligence
from om_ai.core.human_response import HumanResponsePlanner


def test_incomplete_speech_holds():
    sc = SentenceCompletion()
    incomplete = sc.assess("OM I was thinking about my project and")
    assert incomplete["should_wait"] is True
    assert incomplete["complete"] is False

    complete = sc.assess("I had a really bad day.")
    assert complete["complete"] is True
    assert complete["should_wait"] is False


def test_hci_hold_then_commit():
    hci = get_human_conversation_intelligence()
    held = hci.on_final("OM I was thinking about my project and...")
    assert held.get("hold") is True
    assert held.get("commit") is False

    committed = hci.on_final(
        "OM I was thinking about my project and how to fix the bug",
        force=True,
    )
    assert committed.get("commit") is True
    assert committed.get("hold") is False
    assert committed.get("response_plan", {}).get("speak") is True


def test_bad_day_empathy_plan():
    meaning = MeaningReconstruction().reconstruct("I had a really bad day.")
    emo = get_emotional_intelligence().analyze("I had a really bad day.")
    timing = get_timing_engine().decide(meaning, emotion=emo)
    plan = HumanResponsePlanner().plan(timing=timing, emotion=emo, meaning=meaning)
    assert plan.get("wait") is False
    assert plan.get("speak") is True
    intent = (plan.get("intent") or {}).get("intent")
    style = (plan.get("style") or {}).get("system_hint") or ""
    assert "helpdesk" in style.lower() or "faq" in style.lower()
    assert intent in {"comfort", "ask", "answer", "clarify"}
    q = (plan.get("question") or {}).get("question") or ""
    # Careful companion — invite what happened, not a ticket desk
    if intent in {"comfort", "ask"}:
        assert q


def test_partial_does_not_answer():
    hci = get_human_conversation_intelligence()
    pack = hci.on_partial("I was trying to fix")
    assert pack.get("commit") is False
    assert pack.get("mode") == "partial"


def test_companion_runtime_hold_wire():
    from om_ai.core.companion_runtime.companion_runtime import CompanionRuntime

    rt = CompanionRuntime()
    rt.start()
    out = rt.handle_text("OM I was thinking about my project and...", force_commit=False)
    assert out.get("hold") is True
    assert out.get("speak_client") is False
    out2 = rt.handle_text(
        "OM I was thinking about my project and the deploy failed",
        force_commit=True,
    )
    assert out2.get("hold") is not True
    assert (out2.get("spoken") or out2.get("answer") or "").strip()
