class ResponseFusion:

    def combine(self, responses):
        if not responses:
            return {"answer": "", "sources": []}

        # Prefer scored dict responses; fall back to raw strings/objects.
        def _quality(item):
            if isinstance(item, dict):
                return float(item.get("quality") or item.get("score") or 0)
            return 0

        best = max(responses, key=_quality)
        if isinstance(best, dict):
            answer = best.get("answer", best.get("text", ""))
            return {
                "answer": answer if answer is not None else "",
                "sources": list(best.get("sources") or []),
                "model": best.get("model"),
            }

        return {"answer": str(best), "sources": []}
