"""STEP 70 — OM Final Integration Tests (human voice companion path)."""
from __future__ import annotations

from om_ai.core.capability_system import get_capability_system
from om_ai.core.conversation_runtime import get_conversation_loop
from om_ai.core.human_intelligence import get_human_conversation_pipeline
from om_ai.core.multimodal_intelligence import get_multimodal_router
from om_ai.core.presence_runtime import get_presence_engine
from om_ai.core.self_improvement import get_improvement_pipeline


def test_presence_loop_phases():
    pe = get_presence_engine()
    assert pe.start()["phase"] == "waiting"
    assert pe.listening()["phase"] == "listening"
    assert pe.thinking()["phase"] == "thinking"
    assert pe.responding()["phase"] == "responding"
    assert pe.waiting()["phase"] == "waiting"


def test_conversation_hey_om_style():
    pipe = get_human_conversation_pipeline()
    out = pipe.run("Hey OM")
    assert out.get("answer") or out.get("spoken")
    # should not be helpdesk
    assert "how can i help you" not in (out.get("answer") or "").lower()


def test_emotion_exhausted():
    pipe = get_human_conversation_pipeline()
    out = pipe.run("I am exhausted today.")
    assert out.get("need") in {"support_and_listen", "listen_first"}
    assert "tired" in (out.get("answer") or "").lower() or "exhaust" in (out.get("answer") or "").lower()


def test_incomplete_server_story():
    loop = get_conversation_loop()
    pe = get_presence_engine()
    pe.start()
    loop.bind(presence=pe, human_pipeline=get_human_conversation_pipeline())
    out = loop.final_turn("OM yesterday I was fixing my server but...")
    ans = (out.get("answer") or "").lower()
    assert "complete your sentence" not in ans
    assert "server" in ans


def test_multimodal_screen_question():
    mm = get_multimodal_router().route("OM what is wrong here?", screen_ref="capture://demo")
    assert mm.get("multimodal")
    assert mm.get("screen", {}).get("focus") in {"error", "ui", "code"}


def test_capability_catalog():
    caps = get_capability_system()
    ids = {t["id"] for t in caps.list()}
    assert {"browser", "files", "git", "terminal"}.issubset(ids)


def test_self_improvement_offline():
    imp = get_improvement_pipeline()
    pack = imp.after_turn(
        user_message="test",
        answer="How can I help you",
        rating="bad",
    )
    assert pack["observation"]["queued"] is True


def test_bug_celebration_friend():
    pipe = get_human_conversation_pipeline()
    out = pipe.run("I fixed the bug!")
    assert "annoying" in (out.get("answer") or "").lower() or "causing" in (out.get("answer") or "").lower()
