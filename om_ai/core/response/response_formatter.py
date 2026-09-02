"""Response Formatter — ChatGPT-style user answers vs developer brain dump."""
from __future__ import annotations

import os
import re
from typing import Any

from om_ai.understanding.query_kind import query_kind


def response_mode() -> str:
    raw = (os.environ.get("OM_RESPONSE_MODE") or "user").strip().lower()
    if raw in {"developer", "debug", "internal", "dev"}:
        return "developer"
    return "user"


_LEAK = re.compile(
    r"(?i)(\bintent\s*:|\bagents\s*:|\bdomain\s*:|self-critique|self critique|"
    r"knowledge context|reflectionengine|pipeline trace|\bscore\s*:|"
    r"dataset_id|training.hints|\*\*ask:\*\*|^\*\*understanding:\*\*|"
    r"no strong corpus match yet|om-ai brain power|"
    r"heuristic foundation path|passed:\s*true|"
    r"domain\s*`|intent\s*`)"
)

_PIPELINE_HEADINGS = re.compile(
    r"(?im)^#{1,3}\s+(understanding|analysis|technology|architecture|plan|"
    r"validation|evaluation|self-critique|weak areas|knowledge context|"
    r"implementation|next)\b"
)

_PIPELINE_DUMP = re.compile(
    r"(?is)(\*\*ask:\*\*|\*\*understanding:\*\*|##\s+analysis\b|\bagents\s*:|"
    r"self-critique|no strong corpus match yet|om-ai brain power|"
    r"heuristic foundation path|##\s+evaluation\b|##\s+validation\b|"
    r"passed:\s*true|score:\s*0\.|confidence:\s*0\.)"
)


def looks_like_pipeline_dump(text: str) -> bool:
    s = text or ""
    if _PIPELINE_DUMP.search(s):
        return True
    hits = len(_PIPELINE_HEADINGS.findall(s))
    return hits >= 3


def ensure_public_reply(
    question: str,
    text: str,
    payload: dict[str, Any] | None = None,
) -> str:
    """Last-mile gate: never show internal brain chrome to a normal user."""
    if response_mode() == "developer":
        return (text or "").strip()
    fmt = ResponseFormatter()
    data = {**(payload or {}), "question": question, "answer": text or ""}
    if looks_like_pipeline_dump(text or "") or not (text or "").strip():
        out = fmt.format_user_response(data)
    else:
        out = fmt._strip_leaks(text or "")
        if looks_like_pipeline_dump(out) or len(out) < 12:
            out = fmt.format_user_response(data)
    out = fmt._strip_leaks(out)
    if looks_like_pipeline_dump(out) or not out.strip():
        out = fmt._direct_answer(question, data)
    return out.strip() + ("\n" if out.strip() else "")


class ResponseFormatter:
    def format_user_response(self, payload: dict[str, Any] | None = None, **kwargs: Any) -> str:
        data = {**(payload or {}), **kwargs}
        question = str(data.get("question") or "").strip()
        kind = query_kind(question)
        intent = data.get("intent") if isinstance(data.get("intent"), dict) else {}
        intent_name = str(intent.get("intent") or kind).lower()
        if intent_name in {"research", "knowledge"}:
            kind = "knowledge"
        if intent_name == "greeting":
            kind = "greeting"
        if intent_name in {"coding", "debug", "architecture"} and kind != "knowledge":
            kind = "coding"

        if kind == "greeting":
            return "Hello. I am OM. How can I help you today?\n"
        if kind == "knowledge":
            return self._template_knowledge(data, question)
        if kind == "coding":
            return self._template_coding(data, question)
        if kind == "business":
            return self._template_business(data, question)
        return self._template_general(data, question)

    def format_developer_response(self, payload: dict[str, Any] | None = None, **kwargs: Any) -> str:
        data = {**(payload or {}), **kwargs}
        reasoning = data.get("reasoning") if isinstance(data.get("reasoning"), dict) else {}
        md = str(
            data.get("markdown")
            or reasoning.get("markdown")
            or data.get("developer_response")
            or ""
        ).strip()
        if md:
            return md if md.endswith("\n") else md + "\n"
        intent = data.get("intent") if isinstance(data.get("intent"), dict) else {}
        tech = data.get("technology") if isinstance(data.get("technology"), dict) else {}
        evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else {}
        lines = [
            "## Internal Analysis",
            "",
            f"Intent: {intent.get('intent') or 'unknown'}",
            f"Domain: {intent.get('domain') or 'unknown'}",
            f"Technology: {tech.get('technology') or 'none'}",
            f"Evaluation: {evaluation.get('score', evaluation.get('approved'))}",
            "",
            str(data.get("understanding") or reasoning.get("understanding") or ""),
        ]
        return "\n".join(lines).strip() + "\n"

    def _direct_answer(self, question: str, data: dict[str, Any]) -> str:
        try:
            from om_ai.knowledge.facts import lookup_fact

            hit = lookup_fact(question)
            if hit and hit.get("answer"):
                return str(hit["answer"]).strip() + "\n"
        except Exception:
            pass
        q = question.strip()
        if re.search(r"how to.{0,20}start|start work|start today", q, re.I):
            return (
                "Start today with one clear outcome, not a long to-do list.\n\n"
                "1. Write the one thing that must be done by end of day.\n"
                "2. Break it into the first 30-minute task and do that first.\n"
                "3. Remove one blocker (a message, a file, a decision).\n"
                "4. At the end of the day, write what moved and what is next.\n"
            )
        if re.search(r"\bgit\b", q, re.I):
            try:
                from om_ai.knowledge.facts import lookup_fact

                hit = lookup_fact("what is git")
                if hit:
                    return str(hit["answer"]).strip() + "\n"
            except Exception:
                pass
        body = self._strip_leaks(str(data.get("answer") or ""))
        if len(body) >= 40 and not looks_like_pipeline_dump(body):
            return body.strip() + "\n"
        return (
            f"{q}\n\n"
            "Tell me the goal in one sentence and I will answer it directly — "
            "no internal analysis dump, just the next useful step.\n"
        )

    def _template_knowledge(self, data: dict[str, Any], question: str) -> str:
        fact = ""
        try:
            from om_ai.knowledge.facts import lookup_fact

            hit = lookup_fact(question)
            if hit:
                fact = str(hit.get("answer") or "").strip()
        except Exception:
            fact = ""
        if fact:
            return fact + "\n"
        curated = self._direct_answer(question, {**data, "answer": ""})
        if curated and "I will answer this directly" not in curated and "Tell me the goal" not in curated:
            return curated
        raw = self._strip_leaks(str(data.get("answer") or ""))
        if len(raw) >= 40 and not looks_like_pipeline_dump(raw):
            return raw.strip() + "\n"
        return self._direct_answer(question, data)

    def _template_coding(self, data: dict[str, Any], question: str) -> str:
        tech = data.get("technology") if isinstance(data.get("technology"), dict) else {}
        tech_name = str(tech.get("technology") or "").strip()
        if tech_name and tech_name.lower() not in question.lower():
            tech_name = ""
        title = self._coding_title(question, tech_name)
        plan = list(data.get("plan") or [])
        tasks = data.get("tasks") if isinstance(data.get("tasks"), dict) else {}
        if tasks.get("tasks"):
            plan = list(tasks["tasks"])
        architecture = list(data.get("architecture") or [])
        raw = str(data.get("answer") or "")
        sections = self._extract_sections(raw)
        lines: list[str] = [f"# {title}", "", "## Solution", ""]
        if tech_name:
            lines.append(f"We will implement this with **{tech_name}**.")
            lines.append("")
        if architecture:
            lines.append("We will create:")
            for item in architecture[:8]:
                lines.append(f"- {str(item).lstrip('- ').strip()}")
            lines.append("")
        files = sections.get("file structure") or sections.get("project structure")
        blob = f"{question} {tech_name}".lower()
        if "react native" in blob and "login" in blob and "dashboard" not in blob:
            files = self._default_project_structure(question, tech_name) or files
        if not files:
            files = self._default_project_structure(question, tech_name)
        if files:
            lines.append("## Project Structure")
            lines.append("")
            lines.append(files.strip())
            lines.append("")
        if plan:
            lines.append("## Implementation Steps")
            lines.append("")
            for i, step in enumerate(plan, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        testing = sections.get("testing")
        lines.append("## Testing")
        lines.append("")
        if testing:
            for ln in testing.splitlines():
                item = ln.strip().lstrip("-").strip()
                if item:
                    lines.append(f"✓ {item}")
        else:
            lines.extend(["✓ UI validation", "✓ Main user flow", "✓ Error handling"])
        lines.append("")
        nxt = sections.get("next") or sections.get("next steps") or ""
        nxt = re.sub(r"No strong corpus match yet\..*", "", nxt, flags=re.I | re.S).strip()
        install = sections.get("installation") or ""
        if install or nxt:
            lines.append("## Next Steps")
            lines.append("")
            if install:
                lines.append(install.strip())
            if nxt:
                lines.append(nxt)
            lines.append("")
        out = "\n".join(lines).strip() + "\n"
        return self._strip_leaks(out)

    def _template_business(self, data: dict[str, Any], question: str) -> str:
        body = self._strip_leaks(str(data.get("answer") or question))
        return (
            f"{body[:500].strip()}\n\n"
            "Recommendation: decide using the constraints in your question, then validate with data.\n"
        )

    def _template_general(self, data: dict[str, Any], question: str) -> str:
        return self._direct_answer(question, data)

    def _coding_title(self, question: str, tech_name: str) -> str:
        q = re.sub(r"^(create|make|build)\s+", "", question.strip(), flags=re.I)
        q = q.strip().rstrip(".?")
        if q:
            return q.title()
        if tech_name:
            return f"{tech_name.title()} solution"
        return "Solution"

    def _default_project_structure(self, question: str, tech_name: str) -> str:
        blob = f"{question} {tech_name}".lower()
        if "react native" in blob and "login" in blob:
            return (
                "src/\n"
                "├── screens/\n"
                "│   └── LoginScreen.js\n"
                "├── components/\n"
                "├── services/\n"
                "└── styles/\n"
            )
        return ""

    def _extract_sections(self, markdown: str) -> dict[str, str]:
        out: dict[str, str] = {}
        if not markdown:
            return out
        parts = re.split(r"(?m)^##\s+", markdown)
        for part in parts[1:]:
            lines = part.splitlines()
            if not lines:
                continue
            heading = lines[0].strip().lower()
            body = "\n".join(lines[1:]).strip()
            out[heading.split("(")[0].strip()] = body
        return out

    def _strip_leaks(self, text: str) -> str:
        kept: list[str] = []
        skip_block = False
        for ln in (text or "").splitlines():
            low = ln.strip().lower()
            if re.match(
                r"^#{1,3}\s+(understanding|analysis|technology|architecture|plan|"
                r"validation|evaluation|self-critique|weak areas|knowledge context)\s*$",
                low,
            ) or re.match(r"^#{1,3}\s+(implementation|next)\s*$", low):
                skip_block = True
                continue
            if skip_block and re.match(r"^#{1,3}\s+", ln):
                skip_block = False
            if skip_block:
                continue
            if _LEAK.search(ln):
                continue
            if low.startswith("**ask:**") or low.startswith("**understanding:**"):
                continue
            if "no strong corpus match yet" in low or "om-ai brain power" in low:
                continue
            if low.startswith("**agents:**") or low.startswith("**stack inferred:**"):
                continue
            if low.startswith("**plan**") and len(low) < 12:
                continue
            kept.append(ln)
        out = "\n".join(kept)
        out = re.sub(r"\n{3,}", "\n\n", out).strip()
        return out
