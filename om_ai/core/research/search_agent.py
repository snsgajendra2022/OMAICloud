from __future__ import annotations


class SearchAgent:
    """Build focused web-search queries for the Research Engine."""

    def create_queries(
        self,
        question: str,
        understanding: dict | None = None,
        max_queries: int = 5,
    ) -> list[str]:
        question = (question or "").strip()
        if not question:
            return []

        queries: list[str] = [question]
        understanding = understanding or {}

        topic = (
            understanding.get("topic")
            or understanding.get("domain")
            or ""
        )
        intent = str(understanding.get("intent") or "")

        if topic and topic.lower() not in {"general", "unknown"}:
            queries.append(f"{question} {topic}")

        # Freshness / release oriented refinements
        q_low = question.lower()
        if any(s in q_low for s in ("latest", "current", "version", "release", "news", "today")):
            queries.append(f"{question} official release")
            queries.append(f"{question} site:docs OR site:dev OR changelog")

        variants = [
            f"{question} official documentation",
            f"{question} primary source",
            f"{question} latest information",
        ]
        if intent in {"coding", "architecture", "debug", "implementation"}:
            variants.append(f"{question} technical documentation")

        for query in variants:
            if query not in queries:
                queries.append(query)

        # De-dupe while preserving order
        seen: set[str] = set()
        out: list[str] = []
        for q in queries:
            key = q.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            out.append(q)
        return out[:max_queries]
