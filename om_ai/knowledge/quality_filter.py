"""
OM Knowledge Quality Filter

Rejects incorrect knowledge before
it reaches the user.
"""


class KnowledgeQualityFilter:

    def __init__(self):
        pass


    def validate(
        self,
        query: str,
        answer: str,
        domain: str | None = None
    ) -> dict:


        problems = []


        query_lower = query.lower()
        answer_lower = answer.lower()


        # Programming questions should not contain unrelated history
        programming_terms = [
            "react",
            "fastapi",
            "python",
            "javascript",
            "api",
            "database",
            "coding"
        ]


        history_terms = [
            "industrial revolution",
            "steam engines",
            "1800",
            "1900",
            "maxwell electromagnetism"
        ]


        if any(x in query_lower for x in programming_terms):

            for item in history_terms:
                if item in answer_lower:
                    problems.append(
                        f"Unrelated historical context detected: {item}"
                    )


        return {
            "valid": len(problems) == 0,
            "problems": problems
        }