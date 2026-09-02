"""
OM-1.0 Answer Generator

Creates final human readable responses.

Modes:

user:
    Clean ChatGPT style answer

developer:
    Full reasoning/debug information
"""

from __future__ import annotations

from typing import Any


# class AnswerGenerator:
#     def generate(
#         self,
#         request: str,
#         reasoning: dict[str, Any] | None = None,
#         knowledge: dict[str, Any] | list | None = None,
#     ) -> dict[str, Any]:
#         reasoning = reasoning or {}
#         plan = list(reasoning.get("plan") or [])
#         tech = ""
#         understanding = reasoning.get("understanding")
#         if isinstance(understanding, dict):
#             tech = str(understanding.get("technology") or "")
#         sections: list[dict[str, str]] = []
#         lines: list[str] = [f"# Solution\n"]
#         if tech:
#             lines.append(f"We will use **{tech}**.\n")
#             sections.append({"title": "Solution", "body": f"We will use **{tech}**."})
#         if plan:
#             lines.append("## Implementation Steps\n")
#             body = "\n".join(f"{i}. {item}" for i, item in enumerate(plan, 1))
#             lines.append(body)
#             sections.append({"title": "Implementation Steps", "body": body})
#         if isinstance(knowledge, dict) and knowledge.get("answer"):
#             lines.append("\n## Answer\n")
#             lines.append(str(knowledge.get("answer")))
#             sections.append({"title": "Answer", "body": str(knowledge.get("answer"))})
#         answer = "\n".join(lines).strip() + "\n"
#         return {"answer": answer, "sections": sections}


class AnswerGenerator:


    def generate(
        self,
        question: str,
        reasoning: dict[str, Any],
        knowledge: Any = None,
    ) -> str:


        understanding = reasoning.get(
            "understanding",
            ""
        )


        solution = reasoning.get(
            "solution",
            ""
        )


        plan = reasoning.get(
            "plan",
            []
        )


        if solution:

            answer = solution

        else:

            answer = understanding



        sections = []


        if answer:

            sections.append(
                answer.strip()
            )


        if plan:

            sections.append(
                self._format_plan(plan)
            )


        return "\n\n".join(
            sections
        )



    def _format_plan(
        self,
        plan
    ) -> str:


        if not plan:

            return ""


        lines = [
            "Next steps:"
        ]


        for index, item in enumerate(plan, 1):

            lines.append(
                f"{index}. {item}"
            )


        return "\n".join(lines)