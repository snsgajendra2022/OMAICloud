"""Universal multimodal intelligence smoke tests."""
from __future__ import annotations

from pathlib import Path

from om_ai.multimodal.manager import MultimodalManager
from om_ai.multimodal.input_router import InputRouter
from om_ai.generation import GenerationEngine
from om_ai.operating_intelligence.universal import UniversalIntelligence
from om_ai.core.intelligence import run_cognitive_intelligence


def test_input_router_image_ext():
    r = InputRouter().classify(path="shot.png")
    assert r["primary"] == "image"


def test_multimodal_missing_file_safe():
    out = MultimodalManager().process(path="/tmp/no-such-om-image.png", question="what is in this image?")
    assert out["ok"] is True
    assert out["modality"] == "image"


def test_generation_diagram():
    g = GenerationEngine().generate(kind="diagram", question="OM brain loop")
    assert "mermaid" in g["content"]


def test_universal_text_date():
    uni = UniversalIntelligence().run("today date")
    assert "date is" in uni["answer"].lower()
    assert "multimodal_understanding" in uni["stages"]


def test_vision_intent_routes_capability():
    out = run_cognitive_intelligence("analyze this image screenshot")
    assert out["understanding"]["intent"] == "vision_analysis"
    assert out["capability"]["id"] == "vision"
