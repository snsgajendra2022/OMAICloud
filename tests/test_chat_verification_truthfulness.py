from om_ai.core.chat_intelligence.chat_quality_engine import ChatQualityEngine
from om_ai.core.chat_intelligence.verification_engine import VerificationEngine


def test_verification_does_not_claim_truth_from_length_alone():
    result = VerificationEngine().verify(
        "This is a reasonably long answer that sounds complete.",
        message="Explain this topic.",
    )
    assert result["ok"] is True
    assert result["verified"] is False
    assert result["status"] == "unverified"
    assert "independent_verification_not_run" in result["issues"]


def test_verification_only_passes_when_independent_check_is_explicit():
    result = VerificationEngine().verify(
        "This is a reasonably long answer that sounds complete.",
        independent_checks_passed=True,
        verification_evidence=[{"type": "unit_test", "passed": True}],
    )
    assert result["verified"] is True
    assert result["status"] == "verified"
    assert len(result["verification_evidence"]) == 1


def test_verification_reports_failed_independent_check():
    result = VerificationEngine().verify(
        "This is a reasonably long answer that sounds complete.",
        independent_checks_passed=False,
    )
    assert result["verified"] is False
    assert result["status"] == "verification_failed"
    assert "independent_verification_failed" in result["issues"]


def test_quality_engine_separates_usability_from_truth():
    result = ChatQualityEngine().evaluate(
        "A readable answer.",
        optimizer_report={"score": 0.9, "issues": []},
        confidence={"confidence": 0.9},
    )
    assert result["basic_quality_passed"] is True
    assert result["approved"] is True
    assert result["factuality_verified"] is False
    assert result["status"] == "unverified"
    assert "factuality_not_independently_verified" in result["issues"]


def test_quality_engine_blocks_explicit_verification_failure():
    result = ChatQualityEngine().evaluate(
        "A readable answer.",
        optimizer_report={"score": 0.9, "issues": []},
        confidence={"confidence": 0.9},
        verification={"status": "verification_failed", "verified": False},
    )
    assert result["approved"] is False
    assert result["factuality_verified"] is False
    assert "independent_verification_failed" in result["issues"]
