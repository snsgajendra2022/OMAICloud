"""
OM Roadmap status (STEPS 86–105) — what is live vs scaffold vs future training.
"""
from __future__ import annotations

ROADMAP: dict[str, dict[str, str]] = {
    "86": {
        "name": "Tool Intelligence + Autonomous Action Layer",
        "status": "live",
        "path": "om_ai/tools/intelligence/",
    },
    "87": {
        "name": "Internet Intelligence Layer",
        "status": "live",
        "path": "om_ai/internet/",
    },
    "88": {
        "name": "Advanced Knowledge Brain",
        "status": "live",
        "path": "om_ai/knowledge/brain.py",
    },
    "89": {
        "name": "Multimodal Intelligence Fusion",
        "status": "live",
        "path": "om_ai/multimodal/",
    },
    "90": {
        "name": "Vision Intelligence Advanced",
        "status": "partial",
        "path": "om_ai/perception/vision/",
    },
    "91": {
        "name": "Voice Intelligence System",
        "status": "scaffold",
        "path": "om_ai/voice/",
    },
    "92": {
        "name": "Autonomous Coding Intelligence",
        "status": "partial",
        "path": "om_ai/coding_brain + core/agents",
    },
    "93": {
        "name": "Scientific Research Intelligence",
        "status": "planned",
        "path": "",
    },
    "94": {
        "name": "Decision Intelligence System",
        "status": "partial",
        "path": "om_ai/core/cognitive/decision_engine.py",
    },
    "95": {
        "name": "Personal Digital Twin",
        "status": "partial",
        "path": "om_ai/memory (semantic + preferences)",
    },
    "96": {
        "name": "Security & Alignment Intelligence",
        "status": "live",
        "path": "om_ai/tools/intelligence/permission_gate.py",
    },
    "97": {
        "name": "Self Evaluation 2.0",
        "status": "partial",
        "path": "om_ai/core/cognitive/self_evaluator.py",
    },
    "98": {
        "name": "Continuous Improvement System",
        "status": "partial",
        "path": "artifacts/improvement/",
    },
    "99": {
        "name": "Model Training Intelligence",
        "status": "partial",
        "path": "scripts/ + training pipelines",
    },
    "100": {
        "name": "OM Foundation Model",
        "status": "requires_training",
        "path": "OM-1.0 checkpoints",
    },
    "101": {
        "name": "Autonomous Operating System Layer",
        "status": "planned",
        "path": "",
    },
    "102": {
        "name": "Robotics Intelligence Layer",
        "status": "future",
        "path": "",
    },
    "103": {
        "name": "Hardware Integration Intelligence",
        "status": "future",
        "path": "",
    },
    "104": {
        "name": "Manufacturing Intelligence",
        "status": "future",
        "path": "",
    },
    "105": {
        "name": "Global Intelligence Platform",
        "status": "architecture",
        "path": "om_ai/ (system of systems)",
    },
}


def roadmap_status() -> dict[str, dict[str, str]]:
    return dict(ROADMAP)
