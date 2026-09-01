"""Phase 4 validation — do not mark layers complete without these tests."""
from __future__ import annotations

from om_ai.core.reasoning.coding_intelligence import build_coding_blueprint
from om_ai.evaluation.online import evaluate_response
from om_ai.knowledge.embeddings import EmbeddingIndex, embed_text
from om_ai.knowledge.facts import lookup_fact
from om_ai.knowledge.ranker import detect_domain
from om_ai.operating_intelligence import run_cycle
from om_ai.operating_intelligence.knowledge_bridge import research
from om_ai.understanding import understand_language, understand_message
from om_ai.understanding.entities import expand_entities
from om_ai.understanding.intent_detector import detect_intent
from om_ai.understanding.typo_corrector import correct_typos


def test_typo_creat_react_dahsbaord():
    corrected = correct_typos("creat react dahsbaord")
    assert "create" in corrected.lower()
    assert "dashboard" in corrected.lower()
    lang = understand_language("creat react dahsbaord")
    assert lang.canonical_intent.lower() == "create react dashboard"


def test_create_react_login_page_frontend_architecture():
    u = understand_message("create react login page")
    assert u.intent in {"coding", "ui_design"}
    bp = build_coding_blueprint("create react login page", canonical=u.goal)
    assert bp is not None
    assert bp.meta.get("kind") == "login_page"
    assert bp.meta.get("task_type") == "frontend"
    assert "React" in bp.technologies
    md = bp.markdown.lower()
    assert "architecture" in md
    assert "login" in md
    assert "file structure" in md


def test_what_is_pm_in_india_means_prime_minister():
    u = understand_message("what is pm in india")
    assert u.intent == "knowledge"
    blob = (u.understood_meaning + " " + u.goal).lower()
    assert "india" in blob
    assert "prime minister" in blob
    hits = expand_entities("what is pm in india")
    assert any(h.meaning == "Prime Minister" and h.context == "India" for h in hits)
    fact = lookup_fact("what is pm in india")
    assert fact is not None
    assert "Prime Minister" in fact["answer"]
    assert fact["entities"]["place"] == "India"
    assert detect_domain("what is pm in india") == "civics"
    researched = research("what is pm in india")
    assert researched["source"] == "fact_table"
    assert "prime minister" in researched["grounded_reply"].lower()
    cycle = run_cycle("what is pm in india", dry_run=True)
    text = (cycle.response or "").lower()
    assert "prime minister" in text
    assert "india" in text
    ev = evaluate_response("what is pm in india", cycle.response, intent="knowledge")
    assert ev["checks"]["answered_user_intent"] is True
    assert ev["confidence"] > 0.5


def test_creat_python_api_project_backend_architecture():
    corrected = correct_typos("creat python api project")
    assert "create" in corrected.lower()
    assert "python" in corrected.lower()
    lang = understand_language("creat python api project")
    assert "python" in lang.canonical_intent.lower()
    assert "api" in lang.canonical_intent.lower()
    u = understand_message("creat python api project")
    assert u.intent == "coding"
    bp = build_coding_blueprint("creat python api project", canonical=lang.canonical_intent)
    assert bp is not None
    assert bp.meta.get("kind") == "python_api"
    assert bp.meta.get("task_type") == "backend"
    assert "Python" in bp.technologies
    assert "FastAPI" in bp.technologies
    md = bp.markdown.lower()
    assert "architecture" in md
    assert "api" in md
    assert "app/main.py" in md
    assert "dashboard widgets" not in md


def test_embedding_index_vector_search(tmp_path):
    idx = EmbeddingIndex(db_path=str(tmp_path / "vectors.sqlite3"))
    vec = embed_text("FastAPI health endpoint and routers")
    assert vec.shape[0] == 512
    idx.upsert(
        "FastAPI project: app/main.py, routers, Pydantic schemas, tests for /health.",
        tenant_id="t",
        metadata={"domain": "programming", "kind": "api"},
    )
    hits = idx.search("python api health router", tenant_id="t", k=3)
    assert hits
    assert hits[0]["score"] > 0
    assert hits[0]["metadata"]["domain"] == "programming"


def test_intent_definitional_not_coding():
    assert detect_intent("what is pm in india").intent == "knowledge"
    assert detect_intent("create react login page").intent == "coding"
    assert detect_intent("creat python api project").intent == "coding"


def test_reasoning_confidence_present():
    from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

    r = run_reasoning_pipeline("create react login page", retrieve=False)
    assert "confidence" in r
    assert 0.0 <= float(r["confidence"]) <= 1.0
    assert "architecture" in (r.get("markdown") or "").lower()
