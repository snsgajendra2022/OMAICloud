"""
OM-1.0 Self Evaluation Engine

Checks generated answers before
sending to the user.
"""


class SelfEvaluator:


    def __init__(self):

        self.minimum_score = 0.7



    def evaluate(
        self,
        question: str,
        answer: str,
        technology: dict | None = None
    ):


        score = 1.0

        issues = []


        question_lower = question.lower()

        answer_lower = answer.lower()


        # --------------------------------
        # Check answer length
        # --------------------------------

        if len(answer.strip()) < 50:

            score -= 0.3

            issues.append(
                "Answer is too short"
            )


        # --------------------------------
        # Technology validation (coding only)
        # --------------------------------

        coding_ask = False
        try:
            from om_ai.understanding.query_kind import is_coding_task

            coding_ask = is_coding_task(question)
        except Exception:
            coding_ask = False

        if technology and coding_ask:

            expected = technology.get(
                "technology"
            )


            if expected:

                phrase = expected.lower()
                tokens = [t for t in phrase.split() if t]
                matched = phrase in answer_lower or (
                    len(tokens) > 1 and all(t in answer_lower for t in tokens)
                )
                if not matched:

                    score -= 0.3

                    issues.append(
                        f"Missing technology: {expected}"
                    )


        # --------------------------------
        # Requirement validation
        # --------------------------------

        important_words = [

            word

            for word in question_lower.split()

            if len(word) > 4

        ]


        missing = []


        for word in important_words:

            if word not in answer_lower:

                missing.append(word)


        if len(missing) > 3:

            score -= 0.2

            issues.append(
                "Some requested items may be missing"
            )


        approved = (
            score >= self.minimum_score
        )


        return {

            "approved": approved,

            "score": round(
                max(score,0),
                2
            ),

            "issues": issues,

            "improvement_needed":
            not approved

        }