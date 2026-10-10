"""Regression tests for the required 13-case native OM evaluator."""
from scripts.evaluate_om_native_13_cases import CASES, deterministic_checks

def test_suite_has_exactly_thirteen_required_categories():
    assert len(CASES) == 13
    assert [case["id"] for case in CASES] == [
        "01_greeting_hi", "02_greeting_how_are_you", "03_introduction",
        "04_capabilities", "05_ai_explanation", "06_api_definition",
        "07_english_tips", "08_summarization", "09_extraction", "10_logic",
        "11_code_explanation", "12_context_retention", "13_unknown_information",
    ]

def test_short_greeting_is_not_rejected_for_being_short():
    assert all(deterministic_checks("greeting", "Hi!").values())
    assert all(deterministic_checks("greeting", "I'm doing well, thanks.").values())

def test_summary_requires_both_main_ideas():
    assert all(deterministic_checks("summary", "Bees pollinate plants and support food production and ecosystems.").values())
    assert not all(deterministic_checks("summary", "Bees are insects.").values())

def test_extraction_checks_each_requested_fact():
    assert all(deterministic_checks("extraction", "Name: Mira; City: Pune; Favorite language: Python.").values())
    assert not all(deterministic_checks("extraction", "Name: Mira; City: Pune.").values())

def test_context_requires_exact_code_word():
    assert all(deterministic_checks("context", "MAPLE-731").values())
    assert not all(deterministic_checks("context", "MAPLE-713").values())

def test_unknown_information_requires_uncertainty_signal():
    assert all(deterministic_checks("uncertainty", "I cannot tell without a sensor reading.").values())
    assert not all(deterministic_checks("uncertainty", "It is 22 degrees.").values())

def test_logic_check_does_not_accept_invalid_inference():
    assert all(deterministic_checks("logic", "We cannot conclude that some zargs are red.").values())
    assert not all(deterministic_checks("logic", "Yes, some zargs must be red.").values())
