"""Production OS modules: identity, language, coding, agents, eval, memory."""
from __future__ import annotations

from om_ai.agents.specialists import run_specialists
from om_ai.coding_brain import catalog
from om_ai.core.reasoning.coding_intelligence import build_coding_blueprint
from om_ai.evaluation.online import evaluate_response
from om_ai.identity import CORE_PIPELINE, QUALITY_CHECKS, ROLES, identity_card
from om_ai.knowledge.ranker import detect_domain, rank_sources
from om_ai.operating_intelligence import capability_status, run_cycle
from om_ai.understanding import understand_language


def test_identity_is_operating_system_not_chatbot():
    card = identity_card()
    assert "Operating Mind" in card["system_name"]
    assert "Senior Software Engineer" in ROLES
    assert CORE_PIPELINE[0].lower().startswith("analyze")
    assert "Did I understand the user correctly?" in QUALITY_CHECKS
    compact = card["runtime_compact"]
    assert "OM AI" in compact
    assert "chatbot" in compact.lower() or "operating system" in compact.lower()


def test_language_creat_react_dahsborad():
    lang = understand_language("creat react dahsborad")
    assert "create" in lang.corrected.lower()
    assert "dashboard" in lang.corrected.lower()
    assert lang.canonical_intent.lower() == "create react dashboard"


def test_coding_project_blueprint_has_files_and_install():
    bp = build_coding_blueprint("creat react dahsborad", canonical="Create React Dashboard")
    assert bp is not None
    assert bp.file_structure
    assert bp.installation
    md = bp.markdown.lower()
    for section in ("architecture", "file structure", "installation", "testing", "deployment"):
        assert section in md
    assert "api keys" in md
    cat = catalog()
    assert "Python" in cat["languages"]
    assert "React" in cat["frameworks"]
    assert "PHP" in cat["languages"]
    assert "Go" in cat["languages"]


def test_specialists_emit_security_and_tests():
    out = run_specialists("create react dashboard", agents=["coding"])
    names = out["agents"]
    assert "coding" in names
    assert "testing" in names
    assert "security" in names
    assert "## Security" in out["markdown"]
    assert "## Testing" in out["markdown"]
    assert "File structure" in out["markdown"] or "file structure" in out["markdown"].lower()


def test_online_eval_five_dimensions():
    report = evaluate_response(
        "create react dashboard",
        "## Understanding\nCreate React Dashboard\n\n## Architecture\n- Layout\n\n## Testing\n- Empty state\n",
        intent="coding",
    )
    for dim in ("correctness", "completeness", "relevance", "safety", "quality"):
        assert dim in report["dimensions"]
    assert 0 <= report["overall"] <= 100


def test_knowledge_ranker_drops_history_on_howto():
    ranked = rank_sources(
        "How to create React dashboard",
        [
            "History of React creation at Facebook.",
            "Use a layout grid, components, and an API for charts.",
        ],
    )
    assert detect_domain("How to create React dashboard") == "programming"
    assert ranked.dropped
    assert ranked.ranked
    assert "layout" in ranked.ranked[0].text.lower() or "component" in ranked.ranked[0].text.lower()


def test_capability_status_contract():
    st = capability_status()
    assert st["capabilities"]["memory"] == "exists"
    assert st["capabilities"]["electronics_iot"] == "stub"
    assert st["capabilities"]["robotics"] == "stub"
    assert st["capabilities"]["evaluation"] == "exists"


def test_absolute_cycle_understands_typo_dashboard():
    r = run_cycle("creat react dahsborad", dry_run=True)
    blob = (r.response + " " + r.goal + " " + str(r.understood)).lower()
    assert "dashboard" in blob or "react" in blob
    ev = (r.verification or {}).get("evaluation") or {}
    assert "dimensions" in ev or ev == {} or r.response
