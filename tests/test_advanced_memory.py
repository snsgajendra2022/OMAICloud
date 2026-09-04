"""STEP 80.12 / 80.13 — multilingual meaning + advanced memory."""
from __future__ import annotations

from om_ai.language.meaning import extract_meaning
from om_ai.memory import AdvancedMemorySystem, EpisodicMemory, SemanticMemory
from om_ai.memory.memory_manager import MemoryManager


def test_multilingual_hindi_ai_india():
    m = extract_meaning("भारत में AI का भविष्य क्या है?", language="hi")
    assert m["topic"] == "artificial intelligence"
    assert m["country"] == "India"
    assert m["intent"] == "future_analysis"
    assert "artificial intelligence" in m["retrieval_query"]


def test_advanced_memory_layers(tmp_path, monkeypatch):
    monkeypatch.setenv("OM_LONG_TERM_MEMORY", str(tmp_path / "lt.json"))
    mem = AdvancedMemorySystem(tenant_id="t_test", user_id="u_test")
    mem.remember_preference("Prefer short answers")
    eid = mem.remember_experience(
        "What is Laravel?",
        "Laravel uses PHP and requires Composer",
        score=0.9,
    )
    assert eid
    pack = mem.recall("Laravel Composer")
    assert pack["episodic"] or pack["snippets"]
    ctx = mem.context_for_prompt("Laravel")
    assert "Laravel" in ctx or "Composer" in ctx or "preference" in ctx.lower()


def test_memory_manager_legacy_api(tmp_path, monkeypatch):
    monkeypatch.setenv("OM_LONG_TERM_MEMORY", str(tmp_path / "lt2.json"))
    mm = MemoryManager(tenant_id="t2", user_id="u2")
    mm.remember_conversation("hello", "hi there")
    ctx = mm.get_context()
    assert isinstance(ctx, list)


def test_episodic_semantic_direct():
    ep = EpisodicMemory()
    ep.remember("Q1", "A1", score=0.8)
    hits = ep.recall("Q1")
    assert hits
    sem = SemanticMemory()
    sem.remember("User likes FastAPI", kind="fact")
    assert sem.recall("FastAPI")
