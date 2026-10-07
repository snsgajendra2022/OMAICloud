"""
OM Query Intelligence Classifier

Classifies user requests before:
- planning
- retrieval
- agent selection
- response generation

Modes:
- greeting
- knowledge
- coding
- prompt_generation
- research
- ai_research
- date_time
- business
- planning
- debugging
- general
"""


from __future__ import annotations

import re



def clean(text: str) -> str:
    return (text or "").strip()



def is_greeting(text: str) -> bool:

    t = clean(text)

    if not t:
        return False

    # Typo-tolerant good morning / how was your day
    t_norm = re.sub(r"\bmoring\b", "morning", t, flags=re.I)

    if re.search(
        r"\bhow\s+(was|is|are|'s)\s+(your\s+)?(day|date|night|evening|morning)\b",
        t_norm,
        re.I,
    ):
        return True

    return bool(
        re.match(
            r"^(hi+|hello+|hey+|yo|sup|namaste|नमस्ते)"
            r"(\s+there)?[!?.]?$",
            t,
            re.I
        )
    ) or (
        bool(
            re.match(
                r"^(good\s+(morning|evening|afternoon))\b",
                t_norm,
                re.I
            )
        )
        and not re.search(
            r"\b(what(?:'s|\s+is)\s+(?:the\s+)?date|today'?s\s+date)\b",
            t_norm,
            re.I,
        )
    )



def is_date_time(text: str) -> bool:

    t = clean(text)

    # Social "how was your day/date" is NOT a calendar ask
    if re.search(
        r"\bhow\s+(was|is|are|'s)\s+(your\s+)?(day|date|night)\b",
        t,
        re.I,
    ):
        return False

    return bool(
        re.search(
            r"\b("
            r"today'?s?\s+date|current\s+date|what(?:'s|\s+is)\s+(?:the\s+)?date|"
            r"current\s+time|what(?:'s|\s+is)\s+(?:the\s+)?time|"
            r"what\s+day\s+is\s+it|day\s+today"
            r")\b",
            t,
            re.I
        )
    )



def is_prompt_generation(text: str) -> bool:

    t = clean(text)


    return bool(
        re.search(
            r"\b("
            r"create prompt|"
            r"make prompt|"
            r"write prompt|"
            r"generate prompt|"
            r"master prompt|"
            r"cursor prompt|"
            r"ai prompt"
            r")\b",
            t,
            re.I
        )
    )



def is_ai_research(text: str) -> bool:

    t = clean(text)


    return bool(
        re.search(
            r"\b("
            r"ai model|"
            r"dataset|"
            r"training data|"
            r"fine tuning|"
            r"sft|"
            r"llm|"
            r"foundation model|"
            r"machine learning|"
            r"neural network|"
            r"rag"
            r")\b",
            t,
            re.I
        )
    )



def is_research(text: str) -> bool:

    t = clean(text)


    return bool(
        re.search(
            r"\b("
            r"research|"
            r"analyze|"
            r"investigate|"
            r"compare|"
            r"study|"
            r"report"
            r")\b",
            t,
            re.I
        )
    )



def is_definitional(text: str) -> bool:

    t = clean(text)


    if re.search(
        r"\b(create|make|build|implement|fix|debug|code)\b",
        t,
        re.I
    ):
        return False


    return bool(
        re.search(
            r"^\s*(what|who)\s+is\b|"
            r"^\s*(explain|define)\b|"
            r"^\s*how\s+to\b|"
            r"\bwhat\s+is\b",
            t,
            re.I
        )
    )



def is_debugging(text: str) -> bool:

    t = clean(text)


    return bool(
        re.search(
            r"\b("
            r"error|"
            r"bug|"
            r"exception|"
            r"failed|"
            r"not working|"
            r"issue|"
            r"problem"
            r")\b",
            t,
            re.I
        )
    )



def is_coding_task(text: str) -> bool:

    t = clean(text)


    if (
        is_greeting(t)
        or is_definitional(t)
        or is_prompt_generation(t)
    ):
        return False


    return bool(
        re.search(
            r"\b("
            r"create|"
            r"make|"
            r"build|"
            r"implement|"
            r"code|"
            r"coding|"
            r"refactor|"
            r"develop|"
            r"program"
            r")\b|"
            r"\b("
            r"react|"
            r"react native|"
            r"flutter|"
            r"fastapi|"
            r"laravel|"
            r"django|"
            r"vue|"
            r"angular|"
            r"python|"
            r"java"
            r")\b",
            t,
            re.I
        )
    )



def is_business_task(text: str) -> bool:

    t = clean(text)


    return bool(
        re.search(
            r"\b("
            r"market|"
            r"revenue|"
            r"strategy|"
            r"kpi|"
            r"business|"
            r"roi|"
            r"sales"
            r")\b",
            t,
            re.I
        )
    )



def query_kind(text: str) -> str:


    if is_greeting(text):
        return "greeting"


    if is_date_time(text):
        return "date_time"


    if is_prompt_generation(text):
        return "prompt_generation"


    if is_ai_research(text):
        return "ai_research"


    if is_debugging(text):
        return "debugging"


    if is_definitional(text):
        return "knowledge"


    if is_coding_task(text):
        return "coding"


    if is_business_task(text):
        return "business"


    if is_research(text):
        return "research"


    return "general"