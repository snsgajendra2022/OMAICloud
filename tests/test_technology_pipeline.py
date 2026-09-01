"""Technology engine + existing reasoning pipeline (no second brain)."""
from __future__ import annotations

from om_ai.cognition.technology_engine import TechnologyEngine
from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
from om_ai.data.pipeline import DatasetPipeline, DocumentRecord


def test_react_native_not_collapsed_to_react():
    tech = TechnologyEngine().analyze("create react native login and dashboard app")
    assert tech["technology"] == "react native"
    assert tech["category"] == "mobile"
    assert tech["platform"] == "android_ios"


def test_react_web_still_frontend():
    tech = TechnologyEngine().analyze("create react dashboard")
    assert tech["technology"] == "react"
    assert tech["category"] == "frontend"
    assert tech["platform"] == "web"


def test_reasoning_pipeline_uses_technology_and_evaluation():
    result = run_reasoning_pipeline(
        "create react native login and dashboard app",
        retrieve=False,
    )
    tech = result["technology"]
    assert tech["technology"] == "react native"
    assert tech["category"] == "mobile"
    assert tech["platform"] == "android_ios"
    md = result["markdown"].lower()
    assert "## technology" in md
    assert "react native" in md
    assert "mobile" in md
    assert "android_ios" in md
    plan = [str(s).lower() for s in result["plan"]]
    assert any("login" in s for s in plan)
    assert any("dashboard" in s for s in plan)
    assert any("navigation" in s for s in plan)
    assert result["evaluation"]["approved"] is True
    assert "## evaluation" in md
    assert "approved: true" in md


def test_dataset_pipeline_is_not_a_second_brain():
    pipe = DatasetPipeline()
    rows = pipe.process(
        [DocumentRecord(text="A short but valid document about APIs and tests.")]
    )
    assert rows
    assert rows[0].quality_score > 0
