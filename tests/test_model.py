"""Model checkpoint checker tests."""
from __future__ import annotations

from om_ai.backends.checkpoint_checker import check_checkpoint, format_model_status, verify_file


def test_verify_missing_file(tmp_path):
    out = verify_file(tmp_path / "nope.pt")
    assert out["ok"] is False
    assert out["status"] == "MISSING"


def test_check_checkpoint_report_shape():
    report = check_checkpoint(try_load=False)
    assert "checkpoint" in report
    assert "tokenizer" in report
    assert "config" in report
    assert "loading" in report
    text = format_model_status(report)
    assert "Model Status" in text
