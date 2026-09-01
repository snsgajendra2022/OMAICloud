"""Lightweight typo / slang normalizer (no external LLM)."""
from __future__ import annotations

import re

# Common misspellings / chat slang → canonical English tokens.
_WORD_MAP: dict[str, str] = {
    "ned": "need",
    "needd": "need",
    "wan": "want",
    "wanna": "want to",
    "gonna": "going to",
    "gotta": "got to",
    "pls": "please",
    "plz": "please",
    "pleas": "please",
    "thx": "thanks",
    "thanx": "thanks",
    "u": "you",
    "ur": "your",
    "yr": "your",
    "r": "are",
    "im": "i'm",
    "iam": "i am",
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "doesnt": "doesn't",
    "isnt": "isn't",
    "wasnt": "wasn't",
    "havent": "haven't",
    "hasnt": "hasn't",
    "wouldnt": "wouldn't",
    "couldnt": "couldn't",
    "shouldnt": "shouldn't",
    "teh": "the",
    "hte": "the",
    "adn": "and",
    "nad": "and",
    "taht": "that",
    "thta": "that",
    "thne": "then",
    "hten": "then",
    "becuase": "because",
    "becasue": "because",
    "becouse": "because",
    "becoz": "because",
    "bcoz": "because",
    "wih": "with",
    "wit": "with",
    "whit": "with",
    "wiht": "with",
    "fro": "for",
    "fomr": "from",
    "fram": "from",
    "abt": "about",
    "abut": "about",
    "aboutt": "about",
    "udesteing": "understanding",
    "udnerstanding": "understanding",
    "understadning": "understanding",
    "understading": "understanding",
    "understaning": "understanding",
    "udnerstand": "understand",
    "undestand": "understand",
    "understnd": "understand",
    "mistics": "mistakes",
    "mistaks": "mistakes",
    "mistak": "mistake",
    "mainings": "meanings",
    "meanig": "meaning",
    "meanin": "meaning",
    "meening": "meaning",
    "corrcet": "correct",
    "correect": "correct",
    "corect": "correct",
    "corrrect": "correct",
    "thining": "thinking",
    "thinkin": "thinking",
    "tinking": "thinking",
    "complte": "complete",
    "compleate": "complete",
    "complet": "complete",
    "compelete": "complete",
    "anyhow": "anyway",
    "anyhting": "anything",
    "anthing": "anything",
    "someting": "something",
    "somthing": "something",
    "nothin": "nothing",
    "everyting": "everything",
    "evrything": "everything",
    "problm": "problem",
    "probelm": "problem",
    "porblem": "problem",
    "isssue": "issue",
    "isseu": "issue",
    "eror": "error",
    "erro": "error",
    "bugfix": "bug fix",
    "repy": "reply",
    "rely": "reply",
    "anwser": "answer",
    "answr": "answer",
    "responce": "response",
    "reponse": "response",
    "messge": "message",
    "mesage": "message",
    "msg": "message",
    "langauge": "language",
    "languge": "language",
    "speling": "spelling",
    "spellin": "spelling",
    "grammer": "grammar",
    "grammerly": "grammar",
    "intnet": "intent",
    "intenet": "intent",
    "intetn": "intent",
    "requirment": "requirement",
    "requriement": "requirement",
    "reqirement": "requirement",
    "implment": "implement",
    "implemnt": "implement",
    "implimentation": "implementation",
    "architecure": "architecture",
    "architcture": "architecture",
    "feautre": "feature",
    "feture": "feature",
    "fucntion": "function",
    "funciton": "function",
    "compnent": "component",
    "componet": "component",
    "databse": "database",
    "datbase": "database",
    "servr": "server",
    "sever": "server",
    "clinet": "client",
    "moblie": "mobile",
    "aplication": "application",
    "appication": "application",
    "prodction": "production",
    "prodcution": "production",
    "deply": "deploy",
    "deploymnet": "deployment",
    "bestest": "best",
    "likee": "like",
    "then": "then",
    "than": "than",
    "paython": "python",
    "payhthon": "python",
    "pyhton": "python",
    "pytohn": "python",
    "pythn": "python",
    "hanlde": "handle",
    "handel": "handle",
    "hande": "handle",
    "dashbaord": "dashboard",
    "dashbord": "dashboard",
    "dasboard": "dashboard",
    "logn": "login",
    "logni": "login",
    "loging": "login",
    "singin": "sign in",
    "signin": "sign in",
    "singup": "signup",
    "singnup": "signup",
    "registr": "register",
    "regster": "register",
    "mak": "make",
    "maek": "make",
    "creat": "create",
    "crate": "create",
    "pag": "page",
    "paeg": "page",
    "reat": "react",
    "reac": "react",
    "dahsborad": "dashboard",
    "dahsbaord": "dashboard",
    "dahsboard": "dashboard",
    "dashborad": "dashboard",
    "dashbaord": "dashboard",
    "dasboard": "dashboard",
    "memry": "memory",
    "memori": "memory",
    "doker": "docker",
    "dockr": "docker",
    "analisys": "analysis",
    "anaylsis": "analysis",
    "analyis": "analysis",
    "massage": "message",
    "messege": "message",
    "peopwer": "proper",
    "propper": "proper",
}

# Phrase-level repairs for broken chat English.
_PHRASE_MAP: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bi want compl\w*\s+this\s+any\s*how\b", re.I),
        "i want this completed fully",
    ),
    (
        re.compile(r"\bwe\s+ned\s+to\s+this\s+best\s+udesteing\b", re.I),
        "we need the best understanding",
    ),
    (
        re.compile(r"\blike\s+i\s+have\s+mistics\s+in\s+mainings\b", re.I),
        "even when i have mistakes in meanings",
    ),
    (
        re.compile(
            r"\bthne\s+this\s+is\s+corrcet\s+udesteing\s+and\s+thining\s+and\s+reply\b",
            re.I,
        ),
        "then correctly understand, think, and reply",
    ),
    (re.compile(r"\bmy\s+app\s+not\s+run\b", re.I), "my app is not running"),
    (re.compile(r"\bapp\s+not\s+working\b", re.I), "the app is not working"),
    (
        re.compile(r"\b(my|the)\s+(website|site|page|app)\s+slow\b", re.I),
        r"\1 \2 is slow",
    ),
    (
        re.compile(
            r"\b(make|create|build)\s+(.+?)\s+(react|vue|angular|next\.?js)\b",
            re.I,
        ),
        r"create \2 using \3",
    ),
    (re.compile(r"\bmake\s+logn\s+page\s+react\b", re.I), "make login page react"),
    (re.compile(r"\bmake\s+login\s+pag\b", re.I), "make login page"),
    (re.compile(r"\bfix\s+this\s+any\s*how\b", re.I), "fix this completely"),
    (re.compile(r"\bdo\s+it\s+100\s*%?\b", re.I), "complete this fully"),
    (re.compile(r"\bcomplte\s+this\b", re.I), "complete this"),
]

# Unique prefixes for truncated last tokens ("dash" → dashboard).
_PREFIX_WORDS = (
    "dashboard",
    "login",
    "python",
    "react",
    "project",
    "create",
    "fastapi",
    "typescript",
    "javascript",
    "architecture",
    "laravel",
    "django",
    "java",
    "php",
    "golang",
    "rust",
)


def _complete_truncated(s: str) -> str:
    parts = s.split()
    if not parts:
        return s
    last = re.sub(r"[^A-Za-z]", "", parts[-1])
    if len(last) < 3:
        return s
    low = last.lower()
    if low in _WORD_MAP or low in {w.lower() for w in _PREFIX_WORDS}:
        return s
    hits = [w for w in _PREFIX_WORDS if w.startswith(low) and w != low]
    if len(hits) == 1:
        parts[-1] = hits[0]
        return " ".join(parts)
    return s


def correct_typos(text: str) -> str:
    """Normalize common typos / slang while preserving unknown words."""
    s = (text or "").strip()
    if not s:
        return s
    for pat, repl in _PHRASE_MAP:
        s = pat.sub(repl, s)

    def _replace_token(m: re.Match[str]) -> str:
        tok = m.group(0)
        key = tok.lower()
        if key in _WORD_MAP:
            fixed = _WORD_MAP[key]
            # Preserve crude capitalization.
            if tok.isupper():
                return fixed.upper()
            if tok[:1].isupper():
                return fixed[:1].upper() + fixed[1:]
            return fixed
        return tok

    s = re.sub(r"[A-Za-z']+", _replace_token, s)
    return _complete_truncated(s)
