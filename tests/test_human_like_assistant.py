"""Human-like OM assistant — language, context, knowledge, reasoning, coding, format."""
from __future__ import annotations

from om_ai.cognitive import run_cognitive_pipeline
from om_ai.cognitive.explanation import detect_audience, format_for_audience, build_explanation_profile
from om_ai.cognitive.goal_detector import detect_goal
from om_ai.core.reasoning.coding_intelligence import build_coding_blueprint
from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
from om_ai.core.response.format_engine import decide_format, markdown_table
from om_ai.knowledge.selector import select_knowledge
from om_ai.understanding import understand_language, understand_message
from om_ai.understanding.typo_corrector import correct_typos


def test_language_brain_make_login_page_react():
    raw = "make logn page react"
    lang = understand_language(raw)
    assert "login" in lang.corrected.lower()
    gloss = {a.lower(): b.lower() for a, b in lang.tokens}
    assert gloss.get("make") == "create"
    assert gloss.get("logn") == "login"
    assert "ui" in gloss.get("page", "")
    assert "react" in gloss.get("react", "").lower()
    assert lang.canonical_intent.lower() == "create react login page"


def test_understand_message_canonical_login():
    u = understand_message("make logn page react")
    blob = (u.goal + " " + u.understood_meaning + " " + u.public_understanding).lower()
    assert "login" in blob
    assert "react" in blob
    assert u.intent in {"coding", "ui_design"}
    assert (u.meta or {}).get("canonical_intent", "").lower() == "create react login page"


def test_context_add_memory_for_om_ai():
    messages = [
        {"role": "user", "content": "I am building OM AI"},
        {"role": "assistant", "content": "What should we add next?"},
        {"role": "user", "content": "add memory"},
    ]
    u = understand_message("add memory", messages=messages)
    g = detect_goal("add memory", messages=messages)
    assert g.used_context
    assert "memory" in g.goal.lower()
    assert "om ai" in g.goal.lower()
    assert "memory" in u.goal.lower()


def test_goal_docker_this_system():
    messages = [{"role": "user", "content": "Starting a new project for my API"}]
    g = detect_goal("docker this system", messages=messages)
    assert "docker" in g.goal.lower()
    assert "prepare" in g.goal.lower() or "environment" in g.goal.lower() or "dockerfile" in g.goal.lower()


def test_knowledge_selection_react_dashboard():
    profile = select_knowledge(
        "How to create React dashboard?",
        snippets=[
            "Jordan Walke invented React. History of React creation at Facebook in 2013.",
            "Use components, a layout grid, useState, a chart library, CSS, and fetch from an API.",
        ],
    )
    assert "React components" in profile.important
    assert "Layout" in profile.important
    assert any("history" in x.lower() for x in profile.not_important)
    assert profile.dropped
    assert any("component" in k.lower() or "layout" in k.lower() or "chart" in k.lower() for k in profile.kept)


def test_reasoning_website_slow_diagnoses_not_scale():
    r = run_reasoning_pipeline("my website slow", retrieve=False)
    text = (r.get("solution") or "") + "\n" + (r.get("markdown") or "") + "\n" + (r.get("understanding") or "")
    low = text.lower()
    for cause in ("database", "image", "bundle", "cache", "latency"):
        assert cause in low
    # Must not jump straight to scale-up as the only advice.
    assert "increase server" not in low.split("possible causes")[0] if "possible causes" in low else True
    assert r["intent"]["intent"] in {"performance", "debug", "coding"}


def test_coding_intelligence_full_login_system():
    bp = build_coding_blueprint("make app login")
    assert bp is not None
    joined = " ".join(bp.layers).lower()
    for layer in ("frontend", "backend", "database", "authentication", "security", "validation"):
        assert layer in joined
    assert "html file" in " ".join(bp.notes).lower() or "not a single" in " ".join(bp.notes).lower()


def test_explanation_beginner_api_waiter():
    profile = build_explanation_profile("explain API simply for a beginner", intent="knowledge")
    assert profile.audience == "beginner"
    out = format_for_audience(
        "APIs let programs talk over HTTP.",
        profile,
        intent="knowledge",
    )
    assert "waiter" in out.lower()


def test_format_engine_comparison_table():
    spec = decide_format("compare REST vs GraphQL")
    assert spec.mode == "comparison"
    table = markdown_table(["Feature", "A", "B"], [["Caching", "HTTP", "Custom"]])
    assert "| Feature |" in table
    assert "Caching" in table


def test_typo_logn_still_fixed():
    assert "login" in correct_typos("make logn page react").lower()


def test_cognitive_pipeline_still_wired():
    cog = run_cognitive_pipeline("make logn page react")
    assert "login" in cog.corrected.lower()
    assert detect_audience("what is an API eli5") == "beginner"
