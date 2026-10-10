from om_ai.core.intelligence_contract import assess_answer_quality, assess_user_turn


def test_coding_request_routes_to_debugging():
    result = assess_user_turn("My React app has an API error; please debug it")
    assert result.intent == "coding"
    assert result.strategy == "inspect_and_debug"


def test_frustration_is_a_cue_not_a_diagnosis():
    result = assess_user_turn("I tried many times, still not working")
    assert result.emotion == "possible_frustration"
    assert "use_gentle_nonjudgmental_tone" in result.signals


def test_high_impact_action_requires_confirmation():
    result = assess_user_turn("Deploy to production and delete all old records")
    assert result.high_impact_action is True
    assert result.needs_clarification is True
    assert "confirmation_required" in result.signals


def test_empty_input_requests_clarification():
    result = assess_user_turn("   ")
    assert result.needs_clarification is True
    assert "empty_input" in result.signals


def test_answer_quality_flags_empty_answer_and_tool_error():
    result = assess_answer_quality(answer="", user_request="Fix this bug", tool_error=True)
    assert result["passed_basic_checks"] is False
    assert "empty_answer" in result["issues"]
    assert "tool_execution_failed" in result["issues"]


def test_quality_gate_does_not_claim_to_prove_truth():
    result = assess_answer_quality(answer="The answer is 42.", user_request="What is the answer?")
    assert result["passed_basic_checks"] is True
    assert result["requires_independent_verification"] is True
    assert any("do not establish factual truth" in item for item in result["limitations"])
