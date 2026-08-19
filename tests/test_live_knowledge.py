"""Live knowledge — retrieval only, never an LLM."""
from __future__ import annotations

from om_ai.live_knowledge import (
    FreshnessRouter,
    LiveKnowledgeEngine,
    enrich_messages_for_live_knowledge,
    needs_live_knowledge,
)
from om_ai.live_knowledge.fetcher import fetch_url
from om_ai.live_knowledge.html_text import html_to_text
from om_ai.live_knowledge.search import LocalSearchIndex
from om_ai.live_knowledge.sources import urls_for_query


def test_freshness_detects_time_sensitive():
    assert needs_live_knowledge("Who is the current Prime Minister of Nepal?")
    assert needs_live_knowledge("What is the latest Ionic release?")
    assert not needs_live_knowledge("What is recursion?")


def test_enrich_injects_context_without_llm(monkeypatch):
    monkeypatch.delenv("OM_LIVE_KNOWLEDGE_NETWORK", raising=False)
    msgs = [{"role": "user", "content": "What is the latest news today?"}]
    out, meta = enrich_messages_for_live_knowledge(msgs, allow_network=False)
    assert meta["needs_live"] is True
    assert meta["llm_used"] is None
    blob = " ".join(m["content"] for m in out).lower()
    assert "live knowledge" in blob or "network" in blob


def test_enrich_with_local_index_grounds_reply(monkeypatch):
    monkeypatch.delenv("OM_LIVE_KNOWLEDGE_NETWORK", raising=False)
    idx = LocalSearchIndex()
    idx.add(
        "pm",
        "As of the local corpus note, the Prime Minister of Nepal is documented here for tests.",
    )
    msgs = [{"role": "user", "content": "Who is the current Prime Minister of Nepal?"}]
    out, meta = enrich_messages_for_live_knowledge(
        msgs, index=idx, allow_network=False
    )
    assert meta["needs_live"] is True
    assert meta["llm_used"] is None
    assert meta["hits"]
    assert meta.get("grounded_reply")
    assert "User question:" in out[-1]["content"] or "live knowledge" in out[-1]["content"].lower()


def test_fetch_stub_does_not_hit_network_by_default():
    fr = fetch_url("https://example.com", allow_network=False)
    assert fr.stub is True
    assert fr.ok is False


def test_html_to_text_strips_tags():
    text = html_to_text("<html><head><title>T</title></head><body><p>Hello <b>OM</b></p></body></html>")
    assert "Hello" in text and "OM" in text
    assert "<" not in text


def test_local_search_lexical():
    idx = LocalSearchIndex()
    idx.add("a", "OM AI uses licensed corpora and local checkpoints.")
    hits = idx.search("licensed checkpoints")
    assert hits
    assert hits[0].doc_id == "a"


def test_urls_for_nepal_pm():
    urls = urls_for_query("Who is the current Prime Minister of Nepal?")
    assert any("wikipedia.org" in u for u in urls)


def test_router_decision():
    r = FreshnessRouter()
    d = r.decide([{"role": "user", "content": "Explain recursion"}])
    assert d.needs_live is False


def test_engine_offline_time_sensitive():
    engine = LiveKnowledgeEngine(allow_network=False, index=LocalSearchIndex())
    result = engine.collect(
        [{"role": "user", "content": "What is the latest news today?"}]
    )
    assert result.needs_live is True
    assert result.meta["llm_used"] is None
    assert "network" in result.context_block.lower() or result.context_block
