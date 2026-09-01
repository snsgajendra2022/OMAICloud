"""Language Understanding Brain — meaning of words, not only the typed string.

Pipeline: spelling → grammar → language detection → token gloss → canonical task.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from om_ai.understanding.typo_corrector import correct_typos

# Word the user typed → what they meant (domain + chat English).
_TOKEN_GLOSS: dict[str, str] = {
    "make": "create",
    "mak": "create",
    "build": "create",
    "add": "add",
    "fix": "fix",
    "docker": "prepare Docker environment",
    "logn": "login",
    "login": "login",
    "signin": "sign in",
    "signup": "sign up",
    "page": "UI screen",
    "pag": "UI screen",
    "screen": "UI screen",
    "creat": "create",
    "crate": "create",
    "react": "React framework",
    "reat": "React framework",
    "dahsborad": "dashboard",
    "dahsbaord": "dashboard",
    "dahsboard": "dashboard",
    "dashborad": "dashboard",
    "dashbaord": "dashboard",
    "dashboard": "dashboard",
    "vue": "Vue framework",
    "angular": "Angular framework",
    "memory": "memory system",
    "memry": "memory system",
    "dashboard": "dashboard",
    "api": "API",
    "app": "application",
}

_FRAMEWORKS = {
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "nextjs": "Next.js",
    "next": "Next.js",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "laravel": "Laravel",
    "python": "Python",
    "java": "Java",
    "golang": "Go",
    "rust": "Rust",
}

_OBJECTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(login|sign\s*in|auth)\b.*\b(page|screen|ui)\b|\b(page|screen|ui)\b.*\b(login|sign\s*in)\b", re.I), "Login Page"),
    (re.compile(r"\b(signup|sign\s*up|register)\b", re.I), "Signup Page"),
    (re.compile(r"\bdashboard\b", re.I), "Dashboard"),
    (re.compile(r"\bapi\b.*\b(project|service|backend)\b|\b(project|service|backend)\b.*\bapi\b", re.I), "API Project"),
    (re.compile(r"\bmemory\b", re.I), "Memory System"),
    (re.compile(r"\b(login|sign\s*in|auth)\b", re.I), "Login"),
    (re.compile(r"\bapi\b", re.I), "API"),
    (re.compile(r"\bdocker\b", re.I), "Docker Environment"),
]

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_ARABIC = re.compile(r"[\u0600-\u06FF]")
_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
_HINGLISH = re.compile(
    r"\b(kya|hai|hain|nahi|kaise|kahan|bhai|namaste|mujhe|mera|aap)\b",
    re.I,
)


@dataclass
class LanguageUnderstanding:
    original: str
    corrected: str
    language: str
    tokens: list[tuple[str, str]] = field(default_factory=list)
    canonical_intent: str = ""
    grammar_rewritten: bool = False

    def gloss_lines(self) -> list[str]:
        return [f"{src} = {meaning}" for src, meaning in self.tokens]


def detect_language(text: str) -> str:
    t = text or ""
    if _DEVANAGARI.search(t):
        return "hi"
    if _ARABIC.search(t):
        return "ar"
    if _CJK.search(t):
        return "zh"
    if _HINGLISH.search(t):
        return "hi-Latn"
    return "en"


def extract_token_meanings(original: str) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for tok in re.findall(r"[A-Za-z']+", original or ""):
        key = tok.lower()
        if key in seen or key not in _TOKEN_GLOSS:
            continue
        seen.add(key)
        out.append((tok, _TOKEN_GLOSS[key]))
    return out


def canonical_task_title(corrected: str) -> str:
    t = (corrected or "").lower()
    action = "Help"
    if re.search(r"\b(docker|dockerfile)\b", t):
        action = "Prepare"
    elif re.search(r"\b(fix|debug|broken|error|slow)\b", t):
        action = "Diagnose" if "slow" in t else "Fix"
    elif re.search(r"\b(add|enable|integrate)\b", t):
        action = "Add"
    elif re.search(r"\b(make|create|build|using)\b", t):
        action = "Create"
    elif re.search(r"\b(how\s+to|explain|what\s+is)\b", t):
        action = "Explain"

    framework = ""
    for key, label in _FRAMEWORKS.items():
        if re.search(rf"\b{re.escape(key)}\b", t):
            framework = label
            break

    obj = ""
    for pat, label in _OBJECTS:
        if pat.search(t):
            obj = label
            break
    if not obj and "page" in t:
        obj = "Page"

    parts = [action]
    if framework:
        parts.append(framework)
    if obj:
        parts.append(obj)
    if len(parts) == 1:
        return (corrected or "").strip()[:80]
    return " ".join(parts)


def understand_language(text: str) -> LanguageUnderstanding:
    original = (text or "").strip()
    corrected = correct_typos(original)
    tokens = extract_token_meanings(original)
    return LanguageUnderstanding(
        original=original,
        corrected=corrected or original,
        language=detect_language(original),
        tokens=tokens,
        canonical_intent=canonical_task_title(corrected or original),
        grammar_rewritten=corrected.lower() != original.lower(),
    )
