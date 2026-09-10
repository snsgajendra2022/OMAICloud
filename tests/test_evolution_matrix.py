"""Evolution matrix L1–L5 chat routing."""
from om_ai.runtime.evolution_matrix import (
    level_runtime_profile,
    maybe_evolution_reply,
    process_evolution_level,
    resolve_model_id,
)


def test_resolve_all_levels():
    for n in range(1, 6):
        assert resolve_model_id(f"OM-L{n}") == f"OM-L{n}"
        p = level_runtime_profile(f"OM-L{n}")
        assert p["level"] == float(n)
        assert p["model_id"] == f"OM-L{n}"
        assert p["system_hint"]


def test_level_identity_reply():
    text, model, level = maybe_evolution_reply(
        [{"role": "user", "content": "which OM level am I using?"}],
        model="OM-L3",
    )
    assert text is not None
    assert "OM Level 3" in text or "OM-L3" in text
    assert model == "OM-L3"
    assert level == 3.0


def test_profiles_differ_by_level():
    p1 = level_runtime_profile("OM-L1")
    p2 = level_runtime_profile("OM-L2")
    p3 = level_runtime_profile("OM-L3")
    p5 = level_runtime_profile("OM-L5")
    assert p1["prefer_reasoning"] is False
    assert p2["prefer_reasoning"] is True
    assert p3["prefer_tools"] is True
    assert p5["prefer_planning"] is True
    assert p1["style"] != p5["style"]


def test_l5_chatty_prompts_use_native():
    for prompt in ("hi", "hello", "what is the ai", "who are you"):
        text, model, level = maybe_evolution_reply(
            [{"role": "user", "content": prompt}],
            model="OM-L5",
        )
        assert text is None
        assert model == "OM-L5"
        assert level == 5.0


def test_l5_agentic_prompts_use_plain_english():
    text, model, level = maybe_evolution_reply(
        [{"role": "user", "content": "calculate 12 * 50 for our budget projection"}],
        model="OM-L5",
    )
    assert text is not None
    assert "[OM-L5" not in text
    assert "ORGANIZATION MATRIX" not in text
    assert "MASTER GOAL" not in text
    assert "No module named" not in text
    assert "Goal:" in text
    assert model == "OM-L5"
    assert level == 5.0


def test_om5_core_loads_for_sandbox():
    out = process_evolution_level("project costs budget 100", 5.0)
    assert "No module named 'om5_core'" not in out
    assert "[OM-L5" not in out
    assert "Goal:" in out


def test_pipeline_records_selected_level():
    from om_ai.runtime.chat_pipeline import run_chat_pipeline
    from om_ai.runtime.evolution_matrix import level_runtime_profile

    for mid in ("OM-L1", "OM-L2", "OM-L3", "OM-L5"):
        profile = level_runtime_profile(mid)
        out = run_chat_pipeline(
            "hi",
            native_ready=False,
            evolution_level=profile["level"],
            evolution_profile=profile,
        )
        meta = out.get("meta") or {}
        assert meta.get("evolution_level") == profile["level"]
        assert meta.get("evolution_model") == mid
        assert meta.get("evolution_style") == profile["style"]
