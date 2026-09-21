"""
OM Hypothesis Intelligence Engine

Dynamic candidate cause generation before solution commitment.

Responsibilities:

- Generate possible explanations
- Rank probability
- Use context evidence
- Use memory experience
- Identify missing information
- Suggest verification steps

Part of OM reasoning pipeline.
"""

from __future__ import annotations

from typing import Any
import uuid


class HypothesisEngine:
    """
    Generates and ranks possible hypotheses.

    Flow:

    Problem
       |
       v
    Signals
       |
       v
    Candidate hypotheses
       |
       v
    Ranking
       |
       v
    Verification plan
    """


    def __init__(
        self,
        *,
        knowledge_engine=None,
        memory_engine=None,
        reasoning_engine=None,
    ):

        self.knowledge_engine = knowledge_engine
        self.memory_engine = memory_engine
        self.reasoning_engine = reasoning_engine



    def generate(
        self,
        message: str,
        *,
        analysis: dict[str, Any] | None = None,
        memory_hits: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:


        analysis = analysis or {}
        context = context or {}
        memory_hits = memory_hits or []


        hypotheses = []


        # -----------------------------------------
        # 1. Extract reasoning signals
        # -----------------------------------------

        domain = analysis.get(
            "domain",
            "general"
        )

        problem_type = analysis.get(
            "problem_type",
            "unknown"
        )

        symptoms = analysis.get(
            "symptoms",
            []
        )

        constraints = analysis.get(
            "constraints",
            []
        )


        # -----------------------------------------
        # 2. Dynamic generation from reasoning model
        # -----------------------------------------

        if self.reasoning_engine:

            generated = self.reasoning_engine.generate_hypothesis(
                problem=message,
                analysis=analysis,
                context=context
            )

            if generated:

                hypotheses.extend(
                    generated
                )


        # -----------------------------------------
        # 3. Knowledge based hypotheses
        # -----------------------------------------

        if self.knowledge_engine:

            knowledge_candidates = (
                self.knowledge_engine.find_patterns(
                    query=message,
                    domain=domain
                )
            )

            for item in knowledge_candidates or []:

                hypotheses.append(
                    {
                        "id": str(uuid.uuid4()),

                        "claim": item.get(
                            "pattern"
                        ),

                        "reason":
                            "knowledge_pattern",

                        "prior":
                            item.get(
                                "confidence",
                                0.5
                            ),

                        "evidence":
                            item.get(
                                "evidence",
                                []
                            )
                    }
                )



        # -----------------------------------------
        # 4. Generic reasoning fallback
        # -----------------------------------------

        if not hypotheses:

            hypotheses = self._generate_generic(
                problem_type,
                domain,
                symptoms
            )


        # -----------------------------------------
        # 5. Memory reinforcement
        # -----------------------------------------

        self._apply_memory_learning(
            hypotheses,
            memory_hits,
            problem_type
        )


        # -----------------------------------------
        # 6. Apply context scoring
        # -----------------------------------------

        self._score_context(
            hypotheses,
            analysis,
            constraints
        )


        # -----------------------------------------
        # 7. Rank
        # -----------------------------------------

        hypotheses.sort(
            key=lambda x:
            float(
                x.get(
                    "confidence",
                    x.get(
                        "prior",
                        0
                    )
                )
            ),
            reverse=True
        )


        top = (
            hypotheses[0]
            if hypotheses
            else None
        )


        return {

            "hypotheses":
                hypotheses[:5],

            "top":
                top,

            "count":
                len(hypotheses),

            "domain":
                domain,

            "problem_type":
                problem_type,

            "needs_verification":
                True,

            "message_preview":
                message[:150]

        }



    # ==================================================
    # Generic intelligence fallback
    # ==================================================

    def _generate_generic(
        self,
        problem_type,
        domain,
        symptoms
    ):

        return [

            {

                "id": "generic_1",

                "claim":
                    "The issue may come from incorrect assumptions or missing context.",

                "prior":
                    0.45

            },

            {

                "id": "generic_2",

                "claim":
                    "The problem may be caused by environment or configuration differences.",

                "prior":
                    0.40

            },

            {

                "id": "generic_3",

                "claim":
                    "The current approach may need redesign or optimization.",

                "prior":
                    0.35

            }

        ]



    # ==================================================
    # Memory learning
    # ==================================================

    def _apply_memory_learning(
        self,
        hypotheses,
        memory_hits,
        problem_type
    ):

        for memory in memory_hits:

            previous_type = memory.get(
                "problem_type"
            )

            if previous_type != problem_type:
                continue


            for item in hypotheses:

                item["prior"] = min(
                    0.95,
                    float(
                        item.get(
                            "prior",
                            0
                        )
                    ) + 0.05
                )



    # ==================================================
    # Context scoring
    # ==================================================

    def _score_context(
        self,
        hypotheses,
        analysis,
        constraints
    ):

        for item in hypotheses:

            score = float(
                item.get(
                    "prior",
                    0.5
                )
            )


            if analysis.get(
                "high_confidence"
            ):
                score += 0.05


            if constraints:

                score += 0.03


            item["confidence"] = round(
                min(
                    score,
                    0.99
                ),
                3
            )


            item.setdefault(
                "verification_needed",
                [
                    "Collect additional evidence",
                    "Test the hypothesis",
                    "Confirm expected result"
                ]
            )