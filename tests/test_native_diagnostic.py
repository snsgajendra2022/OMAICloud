from scripts.diagnose_native_chat import (
    EMPTY_GENERATION_FALLBACK,
    QUALITY_GATE_WITHHELD_REPLY,
    is_usable_diagnostic_answer,
)


def test_quality_gate_withheld_reply_is_not_a_usable_answer():
    assert not is_usable_diagnostic_answer(QUALITY_GATE_WITHHELD_REPLY)


def test_empty_generation_fallback_is_not_a_usable_answer():
    assert not is_usable_diagnostic_answer(EMPTY_GENERATION_FALLBACK)


def test_empty_answer_is_not_usable():
    assert not is_usable_diagnostic_answer("")
    assert not is_usable_diagnostic_answer(None)


def test_normal_sentence_is_usable():
    assert is_usable_diagnostic_answer("Hello! I am OM, your local AI assistant.")
