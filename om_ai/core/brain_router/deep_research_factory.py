"""Safe DeepResearchEngine factory with a local/live search provider."""
from __future__ import annotations

from typing import Any

from om_ai.core.deep_research.document_reader import DocumentReader
from om_ai.core.deep_research.evidence import Evidence
from om_ai.core.deep_research.information_extractor import InformationExtractor
from om_ai.core.deep_research.research_orchestrator import DeepResearchEngine
from om_ai.core.deep_research.search_agent import SearchAgent
from om_ai.core.deep_research.search_provider import SearchProvider
from om_ai.core.deep_research.source_document import SourceDocument


class LocalLiveSearchProvider(SearchProvider):
    """Best-effort local search: live_knowledge → helpful defaults → empty."""

    def search(self, query: str):
        docs: list[SourceDocument] = []
        q = (query or "").strip()
        if not q:
            return docs

        # Live web/wikipedia pack (optional)
        try:
            from om_ai.runtime.live_answer import fetch_live_pack, live_enabled, network_enabled

            if live_enabled() and network_enabled():
                pack = fetch_live_pack(q, limit=3) or {}
                if pack.get("ok"):
                    answer = str(pack.get("answer") or "").strip()
                    ctx = str(pack.get("context") or "").strip()
                    content = (answer or ctx)[:4000]
                    if content:
                        docs.append(
                            SourceDocument(
                                title="Live knowledge",
                                url=str((pack.get("sources") or ["local://live"])[0]),
                                content=content,
                                source_type="live",
                            )
                        )
        except Exception:
            pass

        # Local fact / helpful default fallback
        if not docs:
            try:
                from om_ai.core.intelligence.real_answer import from_facts, from_helpful_defaults

                text = (from_helpful_defaults(q) or from_facts(q) or "").strip()
                if text:
                    docs.append(
                        SourceDocument(
                            title="OM local knowledge",
                            url="local://om-knowledge",
                            content=text[:4000],
                            source_type="local",
                        )
                    )
            except Exception:
                pass

        return docs


class SafeExtractor(InformationExtractor):
    """Convert extracted dicts into Evidence objects for the report builder."""

    def extract(self, document: dict[str, Any]):
        raw = super().extract(document)
        facts = list(raw.get("facts") or [])
        source = str(raw.get("source") or "unknown")
        claim = " ".join(str(f).strip() for f in facts if str(f).strip())[:1200]
        if not claim:
            claim = str(document.get("content") or "")[:800]
        return Evidence(claim=claim or "(no claim)", source=source, confidence=0.55)


def build_deep_research_engine() -> DeepResearchEngine:
    return DeepResearchEngine(
        search_agent=SearchAgent(LocalLiveSearchProvider()),
        reader=DocumentReader(),
        extractor=SafeExtractor(),
    )
