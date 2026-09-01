"""Tests for OM human-like cognitive pipeline."""
from __future__ import annotations

from om_ai.cognitive import run_cognitive_pipeline
from om_ai.cognitive.goal_detector import detect_goal
from om_ai.understanding.typo_corrector import correct_typos


def test_typo_make_login_page_react():
    assert "login" in correct_typos("make logn page react").lower()
    assert "react" in correct_typos("make logn page react").lower()


def test_context_follow_up_add_memory():
    messages = [
        {"role": "user", "content": "I am building OM AI"},
        {"role": "assistant", "content": "Great — what part next?"},
        {"role": "user", "content": "add memory"},
    ]
    g = detect_goal("add memory", messages=messages)
    assert g.used_context
    assert "memory" in g.goal.lower()
    assert "om ai" in g.goal.lower() or "OM AI" in g.project_topic


def test_cognitive_react_login_intent():
    cog = run_cognitive_pipeline("make logn page react")
    assert "login" in cog.corrected.lower()
    assert cog.intent in {"coding", "ui_design", "chat"}
    assert "react" in " ".join(cog.technologies).lower() or "react" in cog.corrected.lower()


def test_cognitive_docker_system_goal():
    messages = [{"role": "user", "content": "Starting a new project for my API"}]
    g = detect_goal("docker this system", messages=messages)
    assert "docker" in g.goal.lower()
