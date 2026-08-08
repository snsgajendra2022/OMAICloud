from __future__ import annotations

import logging
from typing import Any

from om_ai.actions.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(Tool):
    """Search the knowledge base for relevant documents."""

    name = "knowledge.search"
    description = (
        "Search the private knowledge base for relevant context. "
        "Returns matching text chunks with metadata."
    )
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "k": {"type": "integer"},
        },
        "required": ["query"],
    }

    def __init__(self, knowledge_base: Any, default_k: int = 5, tenant_id: str = "default") -> None:
        self._kb = knowledge_base
        self._default_k = default_k
        self._tenant_id = tenant_id

    def run(self, query: str = "", k: int | None = None, tenant_id: str | None = None, **kwargs: Any) -> ToolResult:
        q = query or kwargs.get("q") or ""
        if not q:
            return ToolResult(False, error="query is required")
        top_k = k if k is not None else self._default_k
        tid = tenant_id or self._tenant_id
        try:
            if hasattr(self._kb, "search_compat"):
                results = self._kb.search_compat(q, k=top_k, tenant_id=tid)
            else:
                # PersistentKnowledgeBase.search(query, tenant_id, k=...)
                try:
                    results = self._kb.search(q, tid, k=top_k)
                except TypeError:
                    results = self._kb.search(q, top_k)
            snippets = []
            for r in results or []:
                if hasattr(r, "text"):
                    snippets.append({
                        "text": r.text,
                        "doc_id": getattr(r, "doc_id", None),
                        "score": getattr(r, "score", None),
                        "tenant_id": getattr(r, "tenant_id", tid),
                    })
                elif isinstance(r, dict):
                    snippets.append(r)
                else:
                    snippets.append({"text": str(r)})
            return ToolResult(ok=True, data=snippets)
        except Exception as exc:
            logger.warning("KnowledgeSearchTool error: %s", exc)
            return ToolResult(ok=False, error=str(exc))
