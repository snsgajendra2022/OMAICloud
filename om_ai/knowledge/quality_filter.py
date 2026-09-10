"""
OM Knowledge Quality Filter

Rejects incorrect / training-template knowledge before it reaches the user.
"""
from __future__ import annotations


class KnowledgeQualityFilter:

    GENESIS_SMELLS = (
        "belongs in the om genesis knowledge map",
        "om genesis knowledge map",
        "genesis-jarvis",
        "variant focus:",
        "practical next step",
        "map this to om ai modules first",
        "bio-digital ideas labeled as research",
        "teach om-1.0 about",
        "for genesis-jarvis",
    )

    def validate(
        self,
        query: str,
        answer: str,
        domain: str | None = None,
    ) -> dict:
        problems: list[str] = []

        query_lower = (query or "").lower()
        answer_lower = (answer or "").lower()

        for smell in self.GENESIS_SMELLS:
            if smell in answer_lower:
                problems.append(f"genesis_template:{smell}")
                break

        # Topic/Explanation/Horizon training layout without real content
        if (
            "## topic" in answer_lower
            and "## explanation" in answer_lower
            and ("## horizon" in answer_lower or "practical next step" in answer_lower)
        ):
            problems.append("genesis_explain_template")

        programming_terms = [
            "react",
            "fastapi",
            "python",
            "javascript",
            "api",
            "database",
            "coding",
            "dashboard",
            "typescript",
        ]
        history_terms = [
            "industrial revolution",
            "steam engines",
            "maxwell electromagnetism",
        ]
        if any(x in query_lower for x in programming_terms):
            for item in history_terms:
                if item in answer_lower:
                    problems.append(f"Unrelated historical context detected: {item}")

        # Programming questions must not answer with DevOps/genesis map fluff only
        if any(x in query_lower for x in ("react", "dashboard", "create", "project")):
            if "devops belongs in the om genesis" in answer_lower:
                problems.append("wrong_domain_genesis_devops")

        return {
            "valid": len(problems) == 0,
            "problems": problems,
        }

    def is_bad_public_answer(self, answer: str) -> bool:
        return not self.validate("", answer or "").get("valid", True)
