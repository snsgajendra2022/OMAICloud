# """
# OM-1.0 Knowledge Ranking Engine

# Ranks retrieved knowledge before reasoning.

# Ranking factors:

# - Keyword relevance
# - Domain match
# - Technology match
# - Topic similarity
# - Content quality
# - Freshness
# """
# from __future__ import annotations

# import re
# from dataclasses import dataclass, field
# from typing import Any

# DOMAINS = (
#     "programming",
#     "engineering",
#     "science",
#     "mathematics",
#     "business",
#     "finance",
#     "education",
#     "medicine",
#     "research",
#     "history",
#     "design",
#     "artificial_intelligence",
#     "civics",
# )

# _DOMAIN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
#     ("programming", re.compile(r"\b(code|python|javascript|react|api|sql|docker|git)\b", re.I)),
#     ("artificial_intelligence", re.compile(r"\b(ai|llm|model|transformer|rag|embedding)\b", re.I)),
#     ("engineering", re.compile(r"\b(architect|system|scale|latency|infra)\b", re.I)),
#     ("mathematics", re.compile(r"\b(math|algebra|calculus|proof|equation)\b", re.I)),
#     ("science", re.compile(r"\b(physics|chemistry|biology|experiment)\b", re.I)),
#     ("business", re.compile(r"\b(market|revenue|strategy|ops|kpi)\b", re.I)),
#     ("finance", re.compile(r"\b(finance|stock|accounting|invoice|tax)\b", re.I)),
#     ("education", re.compile(r"\b(course|lesson|curriculum|student|teach)\b", re.I)),
#     ("medicine", re.compile(r"\b(clinical|patient|diagnosis|drug)\b", re.I)),
#     ("design", re.compile(r"\b(ui|ux|layout|typography|figma)\b", re.I)),
#     ("history", re.compile(r"\b(history|century|ancient|war of)\b", re.I)),
#     ("research", re.compile(r"\b(paper|survey|citation|hypothesis)\b", re.I)),
# ]


# @dataclass
# class RankedSource:
#     text: str
#     score: float
#     domain: str = "general"
#     reason: str = ""


# @dataclass
# class RankResult:
#     domain: str
#     ranked: list[RankedSource] = field(default_factory=list)
#     dropped: list[str] = field(default_factory=list)

#     def to_dict(self) -> dict[str, Any]:
#         return {
#             "domain": self.domain,
#             "ranked": [{"text": r.text[:400], "score": r.score, "reason": r.reason} for r in self.ranked],
#             "dropped": self.dropped,
#         }


# def detect_domain(question: str) -> str:
#     q = question or ""
#     if re.search(r"\b(india|indian|bharat)\b", q, re.I) and re.search(
#         r"\b(pm|prime\s+minister|president|parliament)\b", q, re.I
#     ):
#         return "civics"
#     for name, pat in _DOMAIN_PATTERNS:
#         if pat.search(question or ""):
#             return name
#     return "general"


# def rank_sources(question: str, snippets: list[str] | None = None) -> RankResult:
#     domain = detect_domain(question)
#     q_toks = set(re.findall(r"[a-z0-9]{3,}", (question or "").lower()))
#     howto = bool(re.search(r"\b(how to|create|implement|build)\b", question or "", re.I))
#     ranked: list[RankedSource] = []
#     dropped: list[str] = []
#     for raw in snippets or []:
#         text = (raw or "").strip()
#         if not text:
#             continue
#         low = text.lower()
#         if howto and re.search(r"\b(history of|invented by|founded in)\b", low):
#             dropped.append(text[:200])
#             continue
#         overlap = sum(1 for t in q_toks if t in low)
#         score = overlap / max(1, min(12, len(q_toks)))
#         if domain != "general" and domain.replace("_", " ") in low:
#             score += 0.15
#         ranked.append(RankedSource(text=text, score=round(score, 3), domain=domain, reason="token_overlap"))
#     ranked.sort(key=lambda r: r.score, reverse=True)
#     return RankResult(domain=domain, ranked=ranked[:8], dropped=dropped[:6])
"""
OM-1.0 Knowledge Ranking Engine

Production knowledge ranking before reasoning.

Pipeline:

Retriever
    |
    ↓
Context Filter
    |
    ↓
Knowledge Ranker
    |
    ↓
Reasoning Engine
    |
    ↓
Answer Generator


Ranking signals:

1. Keyword relevance
2. Domain match
3. Technology match
4. Topic similarity
5. Content quality
6. Source trust
7. Freshness
8. Semantic similarity hook
9. Confidence score
"""


from __future__ import annotations


from dataclasses import dataclass, field

from typing import Any

import re
import math
import time



DOMAINS = (

    "programming",
    "engineering",
    "science",
    "mathematics",
    "business",
    "finance",
    "education",
    "medicine",
    "research",
    "history",
    "design",
    "artificial_intelligence",
    "civics",
    "general",

)



DOMAIN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [

    (
        "programming",
        re.compile(
            r"\b(code|python|javascript|react|native|api|sql|docker|git|laravel|java|php)\b",
            re.I
        )
    ),


    (
        "artificial_intelligence",
        re.compile(
            r"\b(ai|llm|model|transformer|rag|embedding|agent)\b",
            re.I
        )
    ),


    (
        "engineering",
        re.compile(
            r"\b(system|architecture|scale|latency|infra|cloud)\b",
            re.I
        )
    ),


    (
        "science",
        re.compile(
            r"\b(physics|chemistry|biology|experiment)\b",
            re.I
        )
    ),


    (
        "finance",
        re.compile(
            r"\b(finance|stock|accounting|invoice|tax)\b",
            re.I
        )
    ),


    (
        "business",
        re.compile(
            r"\b(strategy|market|revenue|sales|kpi)\b",
            re.I
        )
    ),


    (
        "design",
        re.compile(
            r"\b(ui|ux|figma|layout|design)\b",
            re.I
        )
    ),


]



SOURCE_TRUST = {

    "official": 1.0,

    "documentation": 0.95,

    "wikipedia": 0.90,

    "github": 0.85,

    "research": 0.90,

    "unknown": 0.50,

}





@dataclass(slots=True)
class KnowledgeScore:

    text: str

    score: float

    confidence: float

    domain: str = "general"

    reasons: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



    def to_dict(self):

        return {

            "text": self.text[:500],

            "score": self.score,

            "confidence": self.confidence,

            "domain": self.domain,

            "reasons": self.reasons,

        }





@dataclass(slots=True)
class RankResult:

    domain: str

    ranked: list[KnowledgeScore] = field(
        default_factory=list
    )

    dropped: list[str] = field(
        default_factory=list
    )



    def to_dict(self):

        return {

            "domain": self.domain,

            "ranked": [

                x.to_dict()

                for x in self.ranked

            ],

            "dropped": self.dropped

        }





class KnowledgeRanker:



    def __init__(
        self,
        min_score: float = 0.35
    ):

        self.min_score = min_score





    def tokens(
        self,
        text: str
    ) -> set[str]:

        return set(

            re.findall(

                r"[a-zA-Z0-9_]+",

                (text or "").lower()

            )

        )





    def detect_domain(
        self,
        question: str
    ) -> str:


        for name, pattern in DOMAIN_PATTERNS:


            if pattern.search(question):

                return name



        if re.search(
            r"\b(india|indian|bharat)\b",
            question,
            re.I
        ):

            return "civics"



        return "general"





    def keyword_score(
        self,
        query: str,
        document: str
    ) -> float:


        q = self.tokens(query)

        d = self.tokens(document)


        if not q:

            return 0.0



        return len(q & d) / len(q)





    def technology_score(
        self,
        technology: dict | None,
        document: str
    ) -> float:


        if not technology:

            return 0.0



        tech = str(

            technology.get(
                "technology",
                ""
            )

        ).lower()



        if tech and tech in document.lower():

            return 1.0



        return 0.0





    def domain_score(
        self,
        intent: dict | None,
        metadata: dict
    ) -> float:


        if not intent:

            return 0.0



        query_domain = intent.get(
            "domain"
        )


        doc_domain = metadata.get(
            "domain"
        )



        if (
            query_domain
            and doc_domain
            and query_domain == doc_domain
        ):

            return 1.0



        return 0.0





    def quality_score(
        self,
        metadata: dict
    ) -> float:


        try:

            return float(

                metadata.get(
                    "quality_score",
                    0
                )

            )

        except Exception:

            return 0.0





    def source_score(
        self,
        metadata: dict
    ) -> float:


        source = str(

            metadata.get(
                "source",
                "unknown"
            )

        ).lower()



        for key, value in SOURCE_TRUST.items():

            if key in source:

                return value



        return SOURCE_TRUST["unknown"]





    def freshness_score(
        self,
        metadata: dict
    ) -> float:


        created = metadata.get(
            "created_at"
        )


        if not created:

            return 0.5



        try:

            age = time.time() - float(created)


            days = age / 86400


            return max(

                0,

                min(

                    1,

                    1 - days / 365

                )

            )


        except Exception:

            return 0.5





    def semantic_score(
        self,
        query: str,
        document: str
    ) -> float:

        """
        Future embedding model hook.

        Later connect:

        sentence-transformers
        FAISS
        Vector DB

        """

        return 0.0





    def score(
        self,
        query: str,
        document: str,
        *,
        metadata: dict | None = None,
        intent: dict | None = None,
        technology: dict | None = None

    ) -> KnowledgeScore:


        metadata = metadata or {}


        reasons = []


        keyword = self.keyword_score(
            query,
            document
        )


        tech = self.technology_score(
            technology,
            document
        )


        domain = self.domain_score(
            intent,
            metadata
        )


        quality = self.quality_score(
            metadata
        )


        source = self.source_score(
            metadata
        )


        freshness = self.freshness_score(
            metadata
        )


        semantic = self.semantic_score(
            query,
            document
        )



        final = (

            keyword * 0.30

            +

            tech * 0.20

            +

            domain * 0.15

            +

            quality * 0.15

            +

            source * 0.10

            +

            freshness * 0.05

            +

            semantic * 0.05

        )



        if keyword > 0.3:
            reasons.append(
                "keyword match"
            )


        if tech:
            reasons.append(
                "technology match"
            )


        if domain:
            reasons.append(
                "domain match"
            )


        if quality > 0.5:
            reasons.append(
                "high quality"
            )


        if source > 0.7:
            reasons.append(
                "trusted source"
            )



        return KnowledgeScore(

            text=document,

            score=round(
                final,
                4
            ),

            confidence=round(
                min(
                    final + 0.2,
                    1.0
                ),
                3
            ),

            domain=self.detect_domain(
                query
            ),

            reasons=reasons,

            metadata=metadata

        )





    def rank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        *,
        intent=None,
        technology=None

    ) -> list[KnowledgeScore]:


        results = []


        for item in documents:


            result = self.score(

                query,

                item.get(
                    "text",
                    ""
                ),

                metadata=item,

                intent=intent,

                technology=technology

            )



            if result.score >= self.min_score:

                results.append(
                    result
                )



        return sorted(

            results,

            key=lambda x: x.score,

            reverse=True

        )





# Backward compatible function
# Existing OM code can continue using this.


def rank_sources(
    question: str,
    snippets: list[str] | None = None
) -> RankResult:


    ranker = KnowledgeRanker()


    docs = [

        {
            "text": x,
            "source": "unknown"
        }

        for x in snippets or []

    ]


    ranked = ranker.rank(
        question,
        docs
    )


    return RankResult(

        domain=ranker.detect_domain(
            question
        ),

        ranked=ranked,

        dropped=[]

    )