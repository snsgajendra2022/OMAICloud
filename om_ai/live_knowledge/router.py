"""Wire freshness → fetch/search stubs → context for OM-1.0 synthesis only."""
from __future__ import annotations

import os
from typing import Any

from om_ai.live_knowledge.fetcher import fetch_url
from om_ai.live_knowledge.freshness import FreshnessRouter
from om_ai.live_knowledge.search import LocalSearchIndex


def _network_enabled() -> bool:
    return (os.getenv("OM_LIVE_KNOWLEDGE_NETWORK") or "").strip() == "1"


def enrich_messages_for_live_knowledge(
    messages: list[dict],
    *,
    index: LocalSearchIndex | None = None,
    router: FreshnessRouter | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """If query looks time-sensitive, attach retrieval context (never another LLM)."""
    router = router or FreshnessRouter()
    decision = router.decide(messages)
    meta: dict[str, Any] = {
        "needs_live": decision.needs_live,
        "reason": decision.reason,
        "hits": [],
        "fetches": [],
        "llm_used": None,  # always None — OM-1.0 synthesizes later
    }
    if not decision.needs_live:
        return [
            {"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")}
            for m in messages
        ], meta

    blocks: list[str] = [
        "[OM live knowledge — retrieval stubs, not an external LLM]",
        f"Query marked time-sensitive ({decision.reason}).",
    ]

    if index is not None:
        hits = index.search(decision.query, limit=3)
        meta["hits"] = [
            {"doc_id": h.doc_id, "score": h.score, "snippet": h.snippet} for h in hits
        ]
        for h in hits:
            blocks.append(f"- local[{h.doc_id}] ({h.score}): {h.snippet}")

    # Optional URL hint: first http(s) token in the query
    for token in decision.query.split():
        if token.startswith("http://") or token.startswith("https://"):
            fr = fetch_url(token, allow_network=_network_enabled())
            meta["fetches"].append(
                {"url": fr.url, "ok": fr.ok, "stub": fr.stub, "error": fr.error}
            )
            blocks.append(f"- fetch[{fr.url}]: {(fr.text or fr.error or '')[:800]}")
            break
    else:
        # No URL — honest stub note (no silent third-party LLM).
        fr = fetch_url("https://example.invalid/om-live-stub", allow_network=False)
        meta["fetches"].append({"url": fr.url, "ok": False, "stub": True, "error": fr.error})
        blocks.append(
            "- No URL in query; live HTTP fetch not performed. "
            "Answer with OM-1.0 weights and say live data may be unavailable."
        )

    context = "\n".join(blocks)
    out: list[dict[str, str]] = []
    injected = False
    for m in messages:
        role = str(m.get("role") or "user")
        content = str(m.get("content") or "")
        if role == "system" and not injected:
            out.append({"role": "system", "content": f"{content}\n\n{context}".strip()})
            injected = True
        else:
            out.append({"role": role, "content": content})
    if not injected:
        out.insert(0, {"role": "system", "content": context})
    return out, meta
