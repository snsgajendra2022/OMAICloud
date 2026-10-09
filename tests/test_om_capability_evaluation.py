"""Unit tests for deterministic checks in the native capability smoke evaluator."""
from __future__ import annotations

from scripts.evaluate_om_capabilities import deterministic_checks


def test_instruction_following_requires_exactly_three_numbered_items():
    answer = "1. Plan.\n2. Draft.\n3. Review."
    checks = deterministic_checks("instruction_following", answer)
    assert checks["exactly_three_list_items"]
    assert not deterministic_checks("instruction_following", "1. A\n2. B")["exactly_three_list_items"]


def test_knowledge_check_requires_scattering_and_blue_light():
    checks = deterministic_checks(
        "knowledge",
        "Air scatters blue light more strongly than red light.",
    )
    assert all(checks.values())


def test_math_check_uses_numeric_boundary():
    assert deterministic_checks("math", "17 * 23 = 391")["contains_391"]
    assert not deterministic_checks("math", "The number 1391 is here")["contains_391"]


def test_logic_check_rejects_invalid_inference():
    assert deterministic_checks(
        "logic", "We cannot conclude that any zargs are red."
    )["rejects_invalid_conclusion"]


def test_planning_requires_four_numbered_steps():
    answer = "1. Learn Python.\n2. Practice.\n3. Build.\n4. Review."
    assert all(deterministic_checks("planning", answer).values())


def test_coding_check_requires_function_and_asserts():
    answer = (
        "def is_palindrome(text):\n"
        "    normalized = text.replace(' ', '').lower()\n"
        "    return normalized == normalized[::-1]\n"
        "assert is_palindrome('Level')\n"
        "assert is_palindrome('never odd or even')\n"
    )
    assert all(deterministic_checks("coding", answer).values())


def test_debugging_check_requires_numeric_return_fix():
    answer = "def add(a, b):\n    return a + b\nThis returns a number, not a string."
    assert all(deterministic_checks("debugging", answer).values())


def test_structured_output_check_rejects_invalid_json():
    assert deterministic_checks(
        "structured_output", '{"name":"OM","skills":["chat","coding"]}'
    )["valid_json_with_expected_values"]
    assert not deterministic_checks("structured_output", "Here is the JSON: {}")[
        "valid_json_with_expected_values"
    ]


def test_uncertainty_check_rewards_not_inventing_weather():
    answer = "I cannot predict exact weather a month ahead; use a live weather service."
    assert deterministic_checks("uncertainty", answer)["does_not_claim_exact_forecast"]


def test_tool_awareness_asks_for_missing_file():
    answer = "Please upload the file so I can inspect it."
    assert deterministic_checks("tool_awareness", answer)["asks_for_file_or_access"]


def test_context_retention_acknowledgement_check():
    assert deterministic_checks("context_retention", "saved")["acknowledges_saved"]
