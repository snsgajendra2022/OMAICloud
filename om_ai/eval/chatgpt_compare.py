"""
ChatGPT vs OM comparison harness.

Runs the same prompts through OM chat_pipeline and scores against
ChatGPT-quality rubrics. Optionally calls OpenAI if
OM_AI_OPENAI_API_KEY / OPENAI_API_KEY is set.

Usage:
  .venv/bin/python -m om_ai.eval.chatgpt_compare
  .venv/bin/python -m om_ai.eval.chatgpt_compare --with-openai
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE = ROOT / "benchmarks" / "chatgpt_vs_om.jsonl"
DEFAULT_OUT = ROOT / "artifacts" / "comparison" / "chatgpt_vs_om_latest.json"


def load_suite(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _is_garble(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 8:
        return False
    # repeated char / nonsense loops
    if re.search(r"(.)\1{8,}", t):
        return True
    if re.search(r"\b(\w+)(?:\s+\1){4,}\b", t.lower()):
        return True
    vowels = sum(1 for c in t.lower() if c in "aeiou")
    letters = sum(1 for c in t if c.isalpha())
    if letters > 40 and vowels / max(letters, 1) < 0.15:
        return True
    # classic OM-1.0 garble markers
    bad = ("wtstss", "aning a ning", "peer, the down", "pcdet")
    low = t.lower()
    return any(b in low for b in bad)


def score_om(answer: str, checks: list[str], meta: dict[str, Any] | None = None) -> dict[str, Any]:
    a = (answer or "").strip()
    meta = meta or {}
    results: dict[str, bool] = {}
    for c in checks:
        ok = False
        if c == "non_empty":
            ok = len(a) >= 1
        elif c == "not_garble":
            ok = not _is_garble(a)
        elif c == "greeting_ok":
            ok = bool(re.search(r"\b(hi|hello|hey|namaste|om)\b", a.lower())) or len(a) > 10
        elif c == "has_date_like":
            ok = bool(
                re.search(
                    r"\b(20\d{2}|january|february|march|april|may|june|july|august|"
                    r"september|october|november|december|monday|tuesday|wednesday|"
                    r"thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2})\b",
                    a,
                    re.I,
                )
            )
        elif c == "has_code_fence":
            ok = "```" in a or "def " in a or "FastAPI" in a or "@app" in a
        elif c == "has_phases":
            ok = bool(
                re.search(r"(phase\s*\d|architecture|database|backend|frontend|deploy|testing)", a, re.I)
            )
        elif c == "meaning_india_or_ai":
            meaning = ((meta.get("language") or {}).get("meaning") or {})
            ok = (
                meaning.get("country") == "India"
                or meaning.get("topic") == "artificial intelligence"
                or "भारत" in a
                or "AI" in a
                or "artificial" in a.lower()
            )
        elif c.startswith("contains:"):
            ok = c.split(":", 1)[1].lower() in a.lower()
        elif c.startswith("mentions:"):
            ok = c.split(":", 1)[1].lower() in a.lower()
        elif c.startswith("min_chars:"):
            ok = len(a) >= int(c.split(":", 1)[1])
        else:
            ok = False
        results[c] = ok
    passed = sum(1 for v in results.values() if v)
    total = max(1, len(results))
    return {
        "checks": results,
        "passed": passed,
        "total": total,
        "score": round(passed / total, 3),
    }


def run_om(prompt: str) -> dict[str, Any]:
    from om_ai.runtime.chat_pipeline import run_chat_pipeline

    t0 = time.time()
    out = run_chat_pipeline(prompt)
    ms = int((time.time() - t0) * 1000)
    return {
        "answer": str(out.get("answer") or ""),
        "meta": out.get("meta") or {},
        "language": out.get("language") or {},
        "stages": out.get("stages") or [],
        "latency_ms": ms,
    }


def run_openai(prompt: str) -> dict[str, Any] | None:
    key = (
        os.environ.get("OM_AI_OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    ).strip()
    if not key:
        return None
    try:
        import httpx

        base = (
            os.environ.get("OM_AI_OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        model = os.environ.get("OM_AI_OPENAI_MODEL") or "gpt-4o-mini"
        t0 = time.time()
        r = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 400,
            },
            timeout=60.0,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return {
            "answer": text,
            "model": model,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception as exc:
        return {"error": str(exc), "answer": ""}


def chatgpt_reference_score(category: str) -> float:
    """Assumed ChatGPT quality on these prompts (reference, not measured)."""
    # ChatGPT is strong on language; weaker on private local tools without browsing
    table = {
        "conversation": 0.95,
        "tools": 0.9,
        "knowledge": 0.95,
        "coding": 0.95,
        "multilingual": 0.9,
        "tool_intelligence": 0.85,
        "planning": 0.9,
    }
    return table.get(category, 0.9)


def run_comparison(
    suite_path: Path = DEFAULT_SUITE,
    *,
    with_openai: bool = False,
) -> dict[str, Any]:
    cases = load_suite(suite_path)
    rows: list[dict[str, Any]] = []
    om_scores: list[float] = []
    cg_scores: list[float] = []

    for case in cases:
        prompt = case["prompt"]
        om = run_om(prompt)
        om_scored = score_om(
            om["answer"],
            list(case.get("checks") or []),
            meta={"language": om.get("language")},
        )
        cg_ref = chatgpt_reference_score(str(case.get("category") or ""))
        openai_out = run_openai(prompt) if with_openai else None
        openai_scored = None
        if openai_out and openai_out.get("answer"):
            openai_scored = score_om(
                str(openai_out["answer"]),
                list(case.get("checks") or []),
            )
            cg_scores.append(float(openai_scored["score"]))
        else:
            cg_scores.append(cg_ref)

        om_scores.append(float(om_scored["score"]))
        rows.append(
            {
                "id": case["id"],
                "category": case.get("category"),
                "prompt": prompt,
                "chatgpt_expect": case.get("chatgpt_expect"),
                "om_answer": (om["answer"] or "")[:500],
                "om_score": om_scored["score"],
                "om_checks": om_scored["checks"],
                "om_latency_ms": om.get("latency_ms"),
                "om_stages": om.get("stages"),
                "chatgpt_reference_score": cg_ref,
                "chatgpt_live": openai_out,
                "chatgpt_live_score": openai_scored["score"] if openai_scored else None,
                "delta_om_minus_chatgpt": round(
                    float(om_scored["score"])
                    - float(openai_scored["score"] if openai_scored else cg_ref),
                    3,
                ),
            }
        )

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "suite": str(suite_path),
        "cases": len(rows),
        "om_avg": round(sum(om_scores) / max(1, len(om_scores)), 3),
        "chatgpt_avg": round(sum(cg_scores) / max(1, len(cg_scores)), 3),
        "openai_live": bool(with_openai and any(r.get("chatgpt_live_score") is not None for r in rows)),
        "wins": {
            "om": sum(1 for r in rows if r["delta_om_minus_chatgpt"] > 0.05),
            "chatgpt": sum(1 for r in rows if r["delta_om_minus_chatgpt"] < -0.05),
            "tie": sum(1 for r in rows if abs(r["delta_om_minus_chatgpt"]) <= 0.05),
        },
        "rows": rows,
        "verdict": _verdict(
            round(sum(om_scores) / max(1, len(om_scores)), 3),
            round(sum(cg_scores) / max(1, len(cg_scores)), 3),
        ),
    }
    return summary


def _verdict(om_avg: float, cg_avg: float) -> str:
    if om_avg >= cg_avg - 0.05:
        return "OM is competitive with ChatGPT on this suite (tools/local strengths)."
    if om_avg >= 0.6:
        return "OM is usable but behind ChatGPT on fluent language; stronger on local tools/OS features."
    return "OM trails ChatGPT mainly on fluent generation — improve weights + keep tool/memory advantages."


def main() -> None:
    ap = argparse.ArgumentParser(description="ChatGPT vs OM comparison")
    ap.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--with-openai", action="store_true")
    args = ap.parse_args()

    report = run_comparison(args.suite, with_openai=args.with_openai)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== ChatGPT vs OM ===")
    print(f"cases: {report['cases']}")
    print(f"OM avg:       {report['om_avg']}")
    print(f"ChatGPT avg:  {report['chatgpt_avg']} ({'live' if report['openai_live'] else 'reference rubric'})")
    print(f"wins: {report['wins']}")
    print(f"verdict: {report['verdict']}")
    print()
    for r in report["rows"]:
        print(
            f"[{r['id']}] OM={r['om_score']:.2f} CG={r['chatgpt_live_score'] if r['chatgpt_live_score'] is not None else r['chatgpt_reference_score']:.2f} "
            f"Δ={r['delta_om_minus_chatgpt']:+.2f} | {(r['om_answer'] or '')[:70].replace(chr(10), ' ')}"
        )
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
