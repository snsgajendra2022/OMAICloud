from __future__ import annotations


class AnswerPlanner:

    def plan(
        self,
        *,
        message: str,
        intent: str,
        understanding=None,
        reasoning=None,
    ) -> list[str]:

        plan = [
            "Answer the user's actual request",
            "Use only relevant context",
            "Avoid unrelated retrieved material",
        ]

        if understanding:
            plan.append(
                "Respect the meaning and context identified by the understanding engine"
            )

        if reasoning:
            plan.append(
                "Use the reasoning result when it improves correctness"
            )

        if intent in {
            "coding",
            "software_creation",
            "implementation",
        }:
            plan.extend(
                [
                    "Give implementation-oriented output",
                    "Prefer working code when code was requested",
                    "Include only necessary setup or explanation",
                ]
            )

        elif intent in {
            "explanation",
            "knowledge",
            "information_request",
        }:
            plan.extend(
                [
                    "Answer the question directly",
                    "Explain at an appropriate level of detail",
                ]
            )

        elif intent in {
            "casual_conversation",
            "conversation",
            "greeting",
        }:
            plan.extend(
                [
                    "Respond naturally",
                    "Do not inject technical templates",
                ]
            )

        return plan