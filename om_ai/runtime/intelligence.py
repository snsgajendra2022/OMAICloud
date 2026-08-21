"""OM AI intelligence layer: instructions, memory, language, RAG, alignment."""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool = True) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


# ── Language ─────────────────────────────────────────────────────────────────

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_ARABIC = re.compile(r"[\u0600-\u06FF]")
_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_HINGLISH = re.compile(
    r"\b(kya|hai|hain|nahi|nahin|kaise|kahan|kyun|bhai|yaar|namaste|dhanyavad|"
    r"please\s+batao|mujhe|mera|meri|aap|tum)\b",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """Best-effort language tag for reply alignment (not a full NLU stack)."""
    t = (text or "").strip()
    if not t:
        return "en"
    if _DEVANAGARI.search(t):
        return "hi"
    if _ARABIC.search(t):
        return "ar"
    if _CJK.search(t):
        return "zh"
    if _HINGLISH.search(t):
        return "hi-Latn"
    return "en"


def language_instruction(lang: str) -> str:
    mapping = {
        "en": "Reply in clear English.",
        "hi": "Reply in natural Hindi (Devanagari) unless the user asks otherwise.",
        "hi-Latn": "Reply in simple Hinglish (Hindi in Latin script) matching the user.",
        "ar": "Reply in Arabic.",
        "zh": "Reply in Chinese matching the user's script.",
    }
    return mapping.get(lang, "Reply in the same language as the user.")


# ── Memory extraction / recall ───────────────────────────────────────────────

_NAME_SAVE = re.compile(
    r"^\s*(?:my\s+name\s+is|i\s+am|i'm|i\s+go\s+by|call\s+me)\s+([A-Za-z][A-Za-z .'-]{1,60})\s*[.!]?\s*$",
    re.IGNORECASE,
)
_PREF_SAVE = re.compile(
    r"^\s*(?:i\s+prefer|please\s+(?:always\s+)?|remember\s+(?:that\s+)?i)\s+(.{3,200})\s*$",
    re.IGNORECASE,
)
_NAME_ASK = re.compile(
    r"\b(what(?:'s| is)\s+my\s+name|do\s+you\s+know\s+my\s+name|who\s+am\s+i)\b",
    re.IGNORECASE,
)
_REMEMBER_ASK = re.compile(
    r"\b(what\s+do\s+you\s+remember|what\s+do\s+you\s+know\s+about\s+me)\b",
    re.IGNORECASE,
)


def extract_memory_candidates(user_text: str) -> list[dict[str, Any]]:
    """Pull durable facts from user turns for long-term memory."""
    t = (user_text or "").strip()
    out: list[dict[str, Any]] = []
    m = _NAME_SAVE.match(t)
    if m:
        name = m.group(1).strip(" .!")
        if name and len(name.split()) <= 6:
            out.append(
                {
                    "content": f"User's name is {name}.",
                    "kind": "preference",
                    "importance": 0.95,
                    "key": "user_name",
                    "value": name,
                }
            )
    m = _PREF_SAVE.match(t)
    if m:
        pref = m.group(1).strip(" .!")
        if pref:
            out.append(
                {
                    "content": f"User preference: {pref}",
                    "kind": "preference",
                    "importance": 0.8,
                    "key": "preference",
                    "value": pref,
                }
            )
    return out


def _name_from_memories(memories: list[dict[str, Any]]) -> str | None:
    for mem in memories:
        content = str(mem.get("content") or "")
        m = re.search(r"User(?:'s)?\s+name\s+is\s+([A-Za-z][A-Za-z .'-]{1,60})", content, re.I)
        if m:
            return m.group(1).strip(" .!")
        m = re.search(r"\bname\s*[:=]\s*([A-Za-z][A-Za-z .'-]{1,60})", content, re.I)
        if m:
            return m.group(1).strip(" .!")
    return None


def aligned_memory_reply(user_text: str, memories: list[dict[str, Any]]) -> str | None:
    """Deterministic instruction-following answers when memory has the fact."""
    if not memories:
        return None
    if _NAME_ASK.search(user_text or ""):
        name = _name_from_memories(memories)
        if name:
            return f"Your name is {name}."
        return "I don't have your name saved yet. Tell me your name and I'll remember it."
    if _REMEMBER_ASK.search(user_text or ""):
        lines = [str(m.get("content") or "").strip() for m in memories if m.get("content")]
        lines = [x for x in lines if x][:8]
        if not lines:
            return "I don't have saved memories for you yet."
        return "Here's what I remember about you:\n- " + "\n- ".join(lines)
    return None


# ── Retrieval helpers ────────────────────────────────────────────────────────

def load_ui_memories(tenant_id: str, actor: str, *, limit: int = 12) -> list[dict[str, Any]]:
    try:
        from om_ai.api.platform_store import get_platform_store

        items = get_platform_store().list_memories(tenant_id, actor)
        enabled = [m for m in items if m.get("enabled") not in (0, False, "0")]
        enabled.sort(key=lambda m: float(m.get("importance") or 0.5), reverse=True)
        return enabled[:limit]
    except Exception as exc:
        logger.debug("ui memories load failed: %s", exc)
        return []


def save_ui_memory(
    tenant_id: str,
    actor: str,
    *,
    content: str,
    importance: float = 0.7,
    kind: str = "semantic",
) -> None:
    try:
        from om_ai.api.platform_store import get_platform_store

        store = get_platform_store()
        # De-dupe exact content
        existing = store.list_memories(tenant_id, actor)
        if any(str(m.get("content") or "").strip().lower() == content.strip().lower() for m in existing):
            return
        store.create_memory(
            tenant_id, actor, content=content, importance=importance, kind=kind
        )
    except Exception as exc:
        logger.debug("ui memory save failed: %s", exc)


def retrieve_rag(query: str, *, tenant_id: str = "default", k: int = 3) -> list[str]:
    if not _env_flag("OM_CHAT_RAG", True):
        return []
    q = (query or "").strip()
    if len(q) < 4:
        return []
    try:
        from om_ai.api import main as app_main

        kb = getattr(app_main, "knowledge", None)
        if kb is None:
            return []
        hits = kb.search_compat(q, k=k, tenant_id=tenant_id) or []
        texts: list[str] = []
        for h in hits:
            text = str(h.get("text") or "").strip()
            if text and len(text) > 20:
                texts.append(text[:400])
        return texts
    except Exception as exc:
        logger.debug("rag retrieve failed: %s", exc)
        return []


def retrieve_file_snippets(query: str, *, tenant_id: str, actor: str, k: int = 2) -> list[str]:
    """Lightweight local file RAG from uploaded platform files."""
    if not _env_flag("OM_CHAT_FILE_RAG", True):
        return []
    q = (query or "").strip().lower()
    if len(q) < 3:
        return []
    try:
        from om_ai.api.platform_store import get_platform_store

        files = get_platform_store().list_files(tenant_id, actor, q=q)[:k]
        out = []
        for f in files:
            preview = str(f.get("preview") or f.get("content_text") or "").strip()
            if preview:
                out.append(f"File {f.get('name')}: {preview[:350]}")
        return out
    except Exception as exc:
        logger.debug("file rag failed: %s", exc)
        return []


ALIGNMENT_RULES = (
    "Alignment:\n"
    "- Follow the user's instructions precisely.\n"
    "- Prefer helpful, truthful, concise answers.\n"
    "- Use provided Memory and Knowledge when relevant; do not invent personal facts.\n"
    "- Never dump random web/wiki/marketing text.\n"
    "- If you lack information, say so briefly and ask one clarifying question."
)


@dataclass
class IntelligenceBundle:
    extra_system: str = ""
    language: str = "en"
    memories: list[dict[str, Any]] = field(default_factory=list)
    rag_snippets: list[str] = field(default_factory=list)
    direct_reply: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def enrich_for_chat(
    messages: list[dict],
    *,
    tenant_id: str = "default",
    actor: str = "",
    assistant_instructions: str = "",
    project_instructions: str = "",
    compact: bool = True,
) -> IntelligenceBundle:
    """Build instruction + memory + RAG context for one chat turn."""
    user_text = ""
    for m in reversed(messages or []):
        if str(m.get("role") or "") == "user":
            user_text = str(m.get("content") or "").strip()
            break

    lang = detect_language(user_text)
    bundle = IntelligenceBundle(language=lang)

    # Persist new memories from this turn
    if actor and _env_flag("OM_CHAT_MEMORY", True):
        for cand in extract_memory_candidates(user_text):
            save_ui_memory(
                tenant_id,
                actor,
                content=cand["content"],
                importance=float(cand.get("importance") or 0.7),
                kind=str(cand.get("kind") or "semantic"),
            )
            bundle.meta.setdefault("saved_memories", []).append(cand["content"])
            # Aligned acknowledgment (instruction following) instead of base-model junk.
            if cand.get("key") == "user_name" and cand.get("value"):
                name = str(cand["value"])
                if lang in {"hi", "hi-Latn"}:
                    bundle.direct_reply = f"Theek hai — main yaad rakhunga. Aapka naam {name} hai."
                else:
                    bundle.direct_reply = f"Got it — I'll remember that. Your name is {name}."
                bundle.meta["aligned"] = "memory_save"
            elif cand.get("key") == "preference":
                if lang in {"hi", "hi-Latn"}:
                    bundle.direct_reply = "Samajh gaya. Main yeh preference yaad rakhunga."
                else:
                    bundle.direct_reply = "Got it. I'll remember that preference."
                bundle.meta["aligned"] = "memory_save"

    memories: list[dict[str, Any]] = []
    if actor and _env_flag("OM_CHAT_MEMORY", True):
        memories = load_ui_memories(tenant_id, actor)
    bundle.memories = memories

    if bundle.direct_reply:
        return bundle

    # Aligned direct answers for memory questions (instruction following).
    if _env_flag("OM_CHAT_ALIGNMENT", True):
        direct = aligned_memory_reply(user_text, memories)
        if direct:
            # Localize lightly for Hindi greetings-style asks
            if lang in {"hi", "hi-Latn"} and _NAME_ASK.search(user_text or ""):
                name = _name_from_memories(memories)
                if name:
                    direct = f"Aapka naam {name} hai." if lang == "hi" else f"Aapka naam {name} hai."
            bundle.direct_reply = direct
            bundle.meta["aligned"] = "memory"
            return bundle

    parts: list[str] = [ALIGNMENT_RULES, language_instruction(lang)]

    if assistant_instructions.strip():
        parts.append("Assistant instructions:\n" + assistant_instructions.strip()[:1500])
    if project_instructions.strip():
        parts.append("Project instructions:\n" + project_instructions.strip()[:1500])

    if memories:
        mem_lines = [f"- {str(m.get('content') or '').strip()}" for m in memories[:6]]
        mem_lines = [x for x in mem_lines if len(x) > 3]
        if mem_lines:
            block = "Memory about this user:\n" + "\n".join(mem_lines)
            if compact:
                block = block[:500]
            parts.append(block)

    rag: list[str] = []
    if _env_flag("OM_CHAT_RAG", True) and user_text:
        rag = retrieve_rag(user_text, tenant_id=tenant_id, k=2)
        if actor:
            rag.extend(retrieve_file_snippets(user_text, tenant_id=tenant_id, actor=actor, k=1))
    bundle.rag_snippets = rag
    if rag:
        rag_block = "Knowledge (use only if relevant):\n" + "\n".join(
            f"[{i+1}] {s}" for i, s in enumerate(rag[:3])
        )
        if compact:
            rag_block = rag_block[:700]
        parts.append(rag_block)

    # Instruction-following cue for the tiny model
    parts.append(
        "Respond as OM AI to the latest user message. "
        "Answer the request; do not continue unrelated documents."
    )

    extra = "\n\n".join(parts)
    if compact and len(extra) > 900:
        extra = extra[:900]
    bundle.extra_system = extra
    bundle.meta.update(
        {
            "language": lang,
            "memory_count": len(memories),
            "rag_count": len(rag),
            "has_assistant_instructions": bool(assistant_instructions.strip()),
            "has_project_instructions": bool(project_instructions.strip()),
        }
    )
    return bundle
