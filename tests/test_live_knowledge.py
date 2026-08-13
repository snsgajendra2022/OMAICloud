"""Live knowledge stubs — retrieval only, never an LLM."""
from __future__ import annotations

from om_ai.live_knowledge import FreshnessRouter, enrich_messages_for_live_knowledge, needs_live_knowledge
from om_ai.live_knowledge.fetcher import fetch_url
from om_ai.live_knowledge.search import LocalSearchIndex


def test_freshness_detects_time_sensitive():
    assert needs_live_knowledge("Who is the current Prime Minister of Nepal?")
    assert needs_live_knowledge("What is the latest Ionic release?")
    assert not needs_live_knowledge("What is recursion?")


def test_enrich_injects_stub_context_without_llm():
    msgs = [{"role": "user", "content": "What is the latest news today?"}]
    out, meta = enrich_messages_for_live_knowledge(msgs)
    assert meta["needs_live"] is True
    assert meta["llm_used"] is None
    assert out[0]["role"] == "system"
    assert "not an external LLM" in out[0]["content"].lower() or "live knowledge" in out[0]["content"].lower()


def test_fetch_stub_does_not_hit_network_by_default():
    fr = fetch_url("https://example.com", allow_network=False)
    assert fr.stub is True
    assert fr.ok is False


def test_local_search_lexical():
    idx = LocalSearchIndex()
    idx.add("a", "OM AI uses licensed corpora and local checkpoints.")
    hits = idx.search("licensed checkpoints")
    assert hits
    assert hits[0].doc_id == "a"


def test_router_decision():
    r = FreshnessRouter()
    d = r.decide([{"role": "user", "content": "Explain recursion"}])
    assert d.needs_live is False
