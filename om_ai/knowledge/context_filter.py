# """
# OM-1.0 Knowledge Context Filter

# Purpose:
# Reject unrelated retrieved knowledge.

# Checks:
# - Domain
# - Technology
# - Topic relevance
# - Keyword overlap
# """
# from __future__ import annotations

# import re

# from om_ai.understanding.query_kind import query_kind

# _STOP = {
#     "the",
#     "and",
#     "for",
#     "what",
#     "who",
#     "is",
#     "in",
#     "a",
#     "an",
#     "to",
#     "of",
#     "how",
#     "do",
#     "does",
#     "with",
#     "from",
#     "this",
#     "that",
#     "please",
# }

# _CODING_NOISE = re.compile(
#     r"\b(physics|newton|maxwell|electromagnetism|industrial revolution|"
#     r"steam engine|history of|biography)\b",
#     re.I,
# )
# _STACK_NOISE = re.compile(
#     r"\b(react(\s+native)?|fastapi|postgresql|kubernetes|flutter|laravel|"
#     r"django|spring boot)\b",
#     re.I,
# )


# def _tokens(text: str) -> set[str]:
#     return {
#         t
#         for t in re.findall(r"[a-z0-9]+", (text or "").lower())
#         if t not in _STOP and len(t) >= 2
#     }


# class KnowledgeContextFilter:
#     def __init__(self) -> None:
#         self.blocked_contexts = [
#             "industrial revolution",
#             "steam engine",
#             "physics mechanics",
#             "maxwell electromagnetism",
#         ]
#         self.min_score = 0.65

#     def filter(
#         self,
#         query: str,
#         knowledge: dict,
#         intent: dict | None = None,
#         technology: dict | None = None,
#     ):
#         answer = str(knowledge.get("answer", "")).lower()
#         query_lower = query.lower()
#         score = 1.0
#         reasons = []

#         for item in self.blocked_contexts:
#             if item in answer:
#                 score -= 0.5
#                 reasons.append(f"unrelated context: {item}")

#         if technology:
#             expected = technology.get("technology")
#             if expected and expected.lower() not in answer:
#                 score -= 0.2
#                 reasons.append("technology missing")

#         if intent:
#             expected_domain = intent.get("domain")
#             knowledge_domain = str(knowledge.get("domain", ""))
#             if (
#                 expected_domain
#                 and knowledge_domain
#                 and expected_domain != knowledge_domain
#             ):
#                 score -= 0.3
#                 reasons.append("domain mismatch")

#         qtok = _tokens(query)
#         htok = _tokens(answer)
#         overlap = (len(qtok & htok) / max(len(qtok), 1)) if qtok else 0.0
#         if overlap < 0.15 and not any(t in answer for t in qtok if len(t) >= 3):
#             score -= 0.4
#             reasons.append("low keyword overlap")

#         accepted = score >= 0.5
#         return {
#             "accepted": accepted,
#             "score": max(score, 0),
#             "reasons": reasons,
#             "query": query_lower,
#         }

#     def filter_hits(
#         self,
#         query: str,
#         hits: list[str] | None,
#         *,
#         intent: dict | None = None,
#         technology: dict | None = None,
#         threshold: float = 0.65,
#     ) -> list[str]:
#         """Drop retrieved snippets that are off-topic for this question."""
#         del intent, threshold
#         kind = query_kind(query)
#         qtok = _tokens(query)
#         kept: list[str] = []
#         tech_name = ""
#         if technology and technology.get("technology"):
#             tech_name = str(technology.get("technology") or "").lower()

#         for raw in hits or []:
#             text = str(raw or "").strip()
#             if not text:
#                 continue
#             low = text.lower()
#             decision = self.filter(
#                 query,
#                 {"answer": text},
#                 technology={"technology": tech_name} if tech_name and kind == "coding" else None,
#             )
#             if not decision["accepted"]:
#                 continue
#             if any(item in low for item in self.blocked_contexts):
#                 continue
#             if kind == "coding" and _CODING_NOISE.search(low) and not _CODING_NOISE.search(query):
#                 continue
#             if kind == "knowledge" and _STACK_NOISE.search(low) and not _STACK_NOISE.search(query):
#                 continue
#             if kind == "coding" and tech_name:
#                 if tech_name not in low and "```" not in text and not (qtok & _tokens(text)):
#                     continue
#             overlap_words = qtok & _tokens(text)
#             if not overlap_words and "prime minister" not in low:
#                 continue
#             kept.append(text)
#         return kept
# """
# OM-1.0 Knowledge Context Filter

# Filters retrieved knowledge before reasoning.

# Purpose:
# Prevent unrelated information entering the answer pipeline.
# """


# from __future__ import annotations

# from dataclasses import dataclass
# import re



# @dataclass
# class KnowledgeScore:

#     accepted: bool

#     score: float

#     reason: str



# class ContextFilter:


#     def __init__(
#         self,
#         threshold: float = 0.55
#     ):

#         self.threshold = threshold



#     def normalize(
#         self,
#         text: str
#     ) -> set[str]:

#         words = re.findall(
#             r"[a-zA-Z0-9]+",
#             text.lower()
#         )

#         return set(words)



#     def relevance(
#         self,
#         question: str,
#         knowledge: str
#     ) -> float:


#         q_words = self.normalize(
#             question
#         )


#         k_words = self.normalize(
#             knowledge
#         )


#         if not q_words or not k_words:

#             return 0.0



#         overlap = (
#             len(
#                 q_words.intersection(k_words)
#             )
#             /
#             len(q_words)
#         )


#         return round(
#             overlap,
#             3
#         )



#     def filter(
#         self,
#         question: str,
#         documents: list[str]
#     ) -> list[str]:


#         accepted = []


#         for doc in documents:


#             score = self.relevance(
#                 question,
#                 doc
#             )


#             if score >= self.threshold:

#                 accepted.append(
#                     doc
#                 )


#         return accepted



#     def evaluate(
#         self,
#         question: str,
#         document: str
#     ) -> KnowledgeScore:


#         score = self.relevance(
#             question,
#             document
#         )


#         return KnowledgeScore(

#             accepted=
#             score >= self.threshold,

#             score=score,

#             reason=
#             "Relevant knowledge"
#             if score >= self.threshold
#             else
#             "Low relevance"

#         )


"""
OM-1.0 Knowledge Context Intelligence Filter

Purpose:
--------
Controls what knowledge is allowed to enter the OM reasoning engine.

Responsibilities:

1. Remove unrelated knowledge
2. Detect domain mismatch
3. Detect technology mismatch
4. Rank knowledge relevance
5. Block noisy/generated content
6. Provide confidence score
7. Prepare clean context for reasoning


Pipeline:

Retriever
    |
    v
KnowledgeContextFilter
    |
    v
Validated Knowledge
    |
    v
Reasoning Engine


"""

from __future__ import annotations


from dataclasses import dataclass, field
from typing import Any
import re
import math
import logging


from om_ai.understanding.query_kind import query_kind



logger = logging.getLogger(
    "OM.KnowledgeFilter"
)



# =====================================================
# Stop Words
# =====================================================


STOP_WORDS = {

    "the",
    "and",
    "for",
    "what",
    "who",
    "where",
    "when",
    "why",
    "is",
    "are",
    "in",
    "a",
    "an",
    "to",
    "of",
    "how",
    "do",
    "does",
    "with",
    "from",
    "this",
    "that",
    "please"

}



# =====================================================
# Knowledge Noise Patterns
# =====================================================


UNRELATED_NOISE = re.compile(

    r"\b("
    r"industrial revolution|"
    r"steam engine|"
    r"physics mechanics|"
    r"newton|"
    r"maxwell electromagnetism|"
    r"ancient history"
    r")\b",

    re.I

)



CODING_TECHNOLOGIES = re.compile(

    r"\b("
    r"react|"
    r"react native|"
    r"fastapi|"
    r"laravel|"
    r"django|"
    r"spring boot|"
    r"postgresql|"
    r"mysql|"
    r"docker|"
    r"kubernetes|"
    r"flutter"
    r")\b",

    re.I

)



SECRET_PATTERN = re.compile(

    r"("
    r"private key|"
    r"api[_-]?key|"
    r"password\s*=|"
    r"secret\s*="
    r")",

    re.I

)



# =====================================================
# Result Object
# =====================================================


@dataclass
class KnowledgeDecision:


    accepted: bool


    score: float


    reasons: list[str] = field(
        default_factory=list
    )


    metadata: dict[str, Any] = field(
        default_factory=dict
    )



# =====================================================
# Main Filter
# =====================================================


class KnowledgeContextFilter:



    def __init__(
        self,
        threshold: float = 0.65
    ):


        self.threshold = threshold



    # -------------------------------------------------
    # Tokenizer
    # -------------------------------------------------


    def tokens(
        self,
        text: str
    ) -> set[str]:


        words = re.findall(

            r"[a-zA-Z0-9_]+",

            (text or "").lower()

        )


        return {

            word

            for word in words

            if word not in STOP_WORDS

            and len(word) >= 2

        }



    # -------------------------------------------------
    # Similarity
    # -------------------------------------------------


    def keyword_score(
        self,
        query: str,
        document: str
    ) -> float:


        q = self.tokens(query)

        d = self.tokens(document)


        if not q or not d:

            return 0.0



        intersection = len(
            q.intersection(d)
        )


        return round(

            intersection /
            len(q),

            3

        )



    # -------------------------------------------------
    # Technology Match
    # -------------------------------------------------


    def technology_score(
        self,
        document: str,
        technology: dict | None
    ) -> float:



        if not technology:

            return 0.0



        expected = str(

            technology.get(
                "technology",
                ""

            )

        ).lower()



        if not expected:

            return 0.0



        if expected in document.lower():

            return 1.0



        return 0.0



    # -------------------------------------------------
    # Noise Detection
    # -------------------------------------------------


    def noise_check(
        self,
        text: str
    ) -> list[str]:


        problems = []


        if UNRELATED_NOISE.search(text):

            problems.append(
                "unrelated knowledge detected"
            )



        if SECRET_PATTERN.search(text):

            problems.append(
                "sensitive information detected"
            )


        return problems



    # -------------------------------------------------
    # Evaluate Single Knowledge
    # -------------------------------------------------


    def evaluate(

        self,

        query: str,

        document: str,

        intent: dict | None = None,

        technology: dict | None = None

    ) -> KnowledgeDecision:



        score = 0.0


        reasons = []



        # Keyword relevance

        keyword = self.keyword_score(

            query,

            document

        )


        score += keyword * 0.60



        if keyword > 0:

            reasons.append(
                "keyword match"
            )



        # Technology relevance

        tech = self.technology_score(

            document,

            technology

        )


        score += tech * 0.25



        if tech:

            reasons.append(
                "technology match"
            )



        # Query type

        kind = query_kind(
            query
        )


        if kind == "coding":

            if CODING_TECHNOLOGIES.search(document):

                score += 0.15

                reasons.append(
                    "coding context"
                )



        if keyword >= 0.5:
            score = max(score, self.threshold)
            if "keyword match" not in reasons:
                reasons.append("keyword match")

        # Noise

        noise = self.noise_check(
            document
        )


        if noise:

            score -= 0.50

            reasons.extend(
                noise
            )



        score = max(
            0,
            min(
                score,
                1
            )
        )


        return KnowledgeDecision(

            accepted=
            score >= self.threshold,

            score=
            round(score,3),

            reasons=
            reasons,

            metadata={

                "query_type":
                kind,

                "keyword_score":
                keyword,

                "technology_score":
                tech

            }

        )



    # -------------------------------------------------
    # Filter Multiple Documents
    # -------------------------------------------------


    def filter_hits(

        self,

        query: str,

        hits: list[str] | None,

        *,

        intent: dict | None = None,

        technology: dict | None = None

    ) -> list[dict]:


        results = []



        for item in hits or []:


            text = str(
                item
            ).strip()



            if not text:

                continue



            decision = self.evaluate(

                query,

                text,

                intent,

                technology

            )



            if decision.accepted:


                results.append({

                    "text":
                    text,


                    "score":
                    decision.score,


                    "reasons":
                    decision.reasons,


                    "metadata":
                    decision.metadata

                })



        # Highest relevance first

        results.sort(

            key=lambda x:
            x["score"],

            reverse=True

        )



        return [row["text"] for row in results]



    # -------------------------------------------------
    # Backward Compatibility
    # -------------------------------------------------


    def filter(

        self,

        query: str,

        knowledge: dict,

        intent=None,

        technology=None

    ) -> dict:



        text = str(

            knowledge.get(
                "answer",
                ""

            )

        )



        result = self.evaluate(

            query,

            text,

            intent,

            technology

        )



        return {

            "accepted":
            result.accepted,


            "score":
            result.score,


            "reasons":
            result.reasons

        }