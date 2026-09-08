"""Evolution matrix L1–L5 chat routing."""
from om_ai.runtime.evolution_matrix import maybe_evolution_reply, process_evolution_level


def test_l5_chatty_prompts_use_native():
    for prompt in ("hi", "hello", "what is the ai", "who are you"):
        text, model, level = maybe_evolution_reply(
            [{"role": "user", "content": prompt}],
            model="OM-L5",
        )
        assert text is None
        assert model == "OM-L5"
        assert level == 5.0


def test_l5_agentic_prompts_use_matrix():
    text, model, level = maybe_evolution_reply(
        [{"role": "user", "content": "calculate 12 * 50 for our budget projection"}],
        model="OM-L5",
    )
    assert text is not None
    assert "ORGANIZATION MATRIX" in text
    assert "No module named" not in text
    assert model == "OM-L5"
    assert level == 5.0


def test_om5_core_loads_for_sandbox():
    out = process_evolution_level("project costs budget 100", 5.0)
    assert "No module named 'om5_core'" not in out
    assert "ORGANIZATION MATRIX" in out
