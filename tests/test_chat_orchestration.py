"""Phase 1 chat orchestration: system prompts + quality gate."""
from __future__ import annotations

from om_ai.runtime.chat_orchestrator import (
    build_chat_messages,
    generation_config,
    is_low_quality_reply,
    policy_recovery_reply,
)
from om_ai.runtime.system_prompts import (
    DEFAULT_PROMPT_NAME,
    SystemPromptStore,
    active_system_prompt,
)


def test_build_chat_messages_includes_system_and_user():
    msgs = build_chat_messages([{"role": "user", "content": "hii"}], compact=True)
    assert msgs[0]["role"] == "system"
    assert "OM AI" in msgs[0]["content"]
    assert msgs[-1] == {"role": "user", "content": "hii"}


def test_generation_config_defaults(monkeypatch):
    for key in (
        "OM_CHAT_TEMPERATURE",
        "OM_CHAT_TOP_P",
        "OM_CHAT_TOP_K",
        "OM_CHAT_REPETITION_PENALTY",
        "OM_CHAT_MAX_NEW_TOKENS",
        "OM_CHAT_MIN_NEW_TOKENS",
        "OM_CHAT_NO_REPEAT_NGRAM",
        "OM_CHAT_REPETITION_WINDOW",
    ):
        monkeypatch.delenv(key, raising=False)
    cfg = generation_config()
    assert cfg["temperature"] == 0.7
    assert cfg["top_p"] == 0.9
    assert cfg["top_k"] == 50
    assert cfg["repetition_penalty"] == 1.2
    assert cfg["max_new_tokens"] == 96
    assert cfg["no_repeat_ngram_size"] == 3


def test_generation_config_overrides():
    cfg = generation_config(temperature=0.2, max_new_tokens=64)
    assert cfg["temperature"] == 0.2
    assert cfg["max_new_tokens"] == 64


def test_quality_gate_flags_spam_and_loops():
    assert is_low_quality_reply("upgrade upgrade upgrade upgrade") in {"degenerate", "spam"}
    assert is_low_quality_reply("is the preferred form of a membership") == "spam"
    assert is_low_quality_reply("Hi! How can I help you today?") == ""


def test_policy_recovery_never_injects_static():
    assert policy_recovery_reply("hii", reason="spam") is None
    assert policy_recovery_reply("hii", reason="") is None
    assert policy_recovery_reply("explain quantum physics", reason="spam") is None
    assert policy_recovery_reply("नमस्ते", reason="empty", language="hi") is None


def test_cognitive_brain_process_requires_question():
    from om_ai.runtime.chat_orchestrator import run_cognitive_brain

    result = run_cognitive_brain("create react native login and dashboard app")
    tech = result["technology"]
    assert tech["technology"] == "react native"
    assert tech["category"] == "mobile"
    assert tech["platform"] == "android_ios"
    assert result["evaluation"]["approved"] is True
    user = (result.get("user_response") or result.get("answer") or "").lower()
    assert "react native" in user
    assert "agents:" not in user
    assert "self-critique" not in user
    assert any("login" in str(t).lower() for t in (result["tasks"] or {}).get("tasks") or [])
    from om_ai.runtime.chat_orchestrator import looks_like_assistant_chitchat

    assert looks_like_assistant_chitchat("Hi! How can I help you today?")
    assert not looks_like_assistant_chitchat(
        "low k performance, this could be found at cold speeds by 35% cheaper"
    )


def test_system_prompt_store_seed(tmp_path):
    store = SystemPromptStore(str(tmp_path / "prompts.sqlite3"))
    active = store.get_active()
    assert active is not None
    assert active["name"] == DEFAULT_PROMPT_NAME
    assert "OM AI" in active["content"]
    text = active_system_prompt(compact=True)
    assert "OM AI" in text
