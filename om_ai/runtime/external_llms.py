"""Optional external LLM connectors (OpenAI-compatible + Anthropic).

OM-1.0 remains the default owned brain. External providers run only when the
user enables them in Settings and supplies an API key (or matching env var).
"""
from __future__ import annotations

import os
from typing import Any

import httpx

# Provider id → connector config
LLM_CATALOG: dict[str, dict[str, Any]] = {
    "om": {
        "name": "OM-1.0",
        "vendor": "OM AI",
        "owned": True,
        "style": "om_native",
        "model": "OM-1.0",
    },
    "gpt": {
        "name": "GPT",
        "vendor": "OpenAI",
        "style": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "env_keys": ("OM_AI_OPENAI_API_KEY", "OPENAI_API_KEY"),
    },
    "claude": {
        "name": "Claude",
        "vendor": "Anthropic",
        "style": "anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-3-5-haiku-latest",
        "env_keys": ("OM_AI_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    },
    "gemini": {
        "name": "Gemini",
        "vendor": "Google",
        "style": "openai",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-2.0-flash",
        "env_keys": ("OM_AI_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"),
    },
    "llama": {
        "name": "Llama",
        "vendor": "Meta (via Groq)",
        "style": "openai",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "env_keys": ("OM_AI_LLAMA_API_KEY", "GROQ_API_KEY"),
    },
    "mistral": {
        "name": "Mistral",
        "vendor": "Mistral AI",
        "style": "openai",
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-small-latest",
        "env_keys": ("OM_AI_MISTRAL_API_KEY", "MISTRAL_API_KEY"),
    },
    "qwen": {
        "name": "Qwen",
        "vendor": "Alibaba",
        "style": "openai",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
        "env_keys": ("OM_AI_QWEN_API_KEY", "DASHSCOPE_API_KEY"),
    },
    "deepseek": {
        "name": "DeepSeek",
        "vendor": "DeepSeek",
        "style": "openai",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "env_keys": ("OM_AI_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
    },
    "grok": {
        "name": "Grok",
        "vendor": "xAI",
        "style": "openai",
        "base_url": "https://api.x.ai/v1",
        "model": "grok-2-latest",
        "env_keys": ("OM_AI_GROK_API_KEY", "XAI_API_KEY"),
    },
}

EXTERNAL_IDS = tuple(k for k, v in LLM_CATALOG.items() if not v.get("owned"))


def normalize_provider_id(model: str | None) -> str | None:
    """Map request model aliases to a catalog id."""
    raw = (model or "").strip().lower()
    if not raw:
        return None
    aliases = {
        "om": "om",
        "om-1.0": "om",
        "om1.0": "om",
        "om_native": "om",
        "om-l1": "om",
        "om-l2": "om",
        "om-l3": "om",
        "om-l4": "om",
        "om-l5": "om",
        "om-5.0": "om",
        "om-5": "om",
        "openai": "gpt",
        "gpt-4": "gpt",
        "gpt-4o": "gpt",
        "gpt-4o-mini": "gpt",
        "chatgpt": "gpt",
        "anthropic": "claude",
        "claude-3": "claude",
        "google": "gemini",
        "meta": "llama",
        "llama3": "llama",
        "groq": "llama",
    }
    if raw.startswith("om-l") or raw.startswith("om-level"):
        return "om"
    if raw in LLM_CATALOG:
        return raw
    if raw in aliases:
        return aliases[raw]
    for pid, meta in LLM_CATALOG.items():
        name = str(meta.get("name") or "").lower()
        if raw == name or raw.startswith(pid):
            return pid
    return None


def _env_key(names: tuple[str, ...] | list[str]) -> str:
    for n in names:
        val = (os.getenv(n) or "").strip()
        if val:
            return val
    return ""


def resolve_api_key(provider_id: str, stored_keys: dict[str, str] | None = None) -> str:
    meta = LLM_CATALOG.get(provider_id) or {}
    if meta.get("owned"):
        return ""
    stored = (stored_keys or {}).get(provider_id) or ""
    if str(stored).strip() and str(stored).strip() not in {"••••", "****", "***"}:
        return str(stored).strip()
    return _env_key(tuple(meta.get("env_keys") or ()))


def provider_ready(
    provider_id: str,
    *,
    enabled: dict[str, bool] | None = None,
    stored_keys: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason)."""
    meta = LLM_CATALOG.get(provider_id)
    if not meta:
        return False, f"Unknown provider: {provider_id}"
    if meta.get("owned"):
        return True, "owned"
    en = enabled or {}
    if not en.get(provider_id):
        return False, f"{meta['name']} is disabled in Settings → AI"
    if not resolve_api_key(provider_id, stored_keys):
        envs = ", ".join(meta.get("env_keys") or [])
        return (
            False,
            f"{meta['name']} needs an API key in Settings → AI (or env: {envs})",
        )
    return True, "ready"


def _normalize_messages(messages: list[dict]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages or []:
        role = str(m.get("role") or "user")
        content = m.get("content")
        if content is None:
            content = ""
        elif not isinstance(content, str):
            content = str(content)
        out.append({"role": role, "content": content})
    return out


def chat_via_openai_compat(
    messages: list[dict],
    *,
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 1.0,
) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": _normalize_messages(messages),
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "top_p": float(top_p),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=payload, headers=headers)
        if r.status_code >= 400:
            detail = r.text[:400]
            raise RuntimeError(f"External LLM HTTP {r.status_code}: {detail}")
        data = r.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected LLM payload: {data!r}") from exc


def chat_via_anthropic(
    messages: list[dict],
    *,
    api_key: str,
    model: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    system_parts: list[str] = []
    converted: list[dict[str, str]] = []
    for m in _normalize_messages(messages):
        role = m["role"]
        if role == "system":
            system_parts.append(m["content"])
            continue
        if role not in {"user", "assistant"}:
            role = "user"
        converted.append({"role": role, "content": m["content"]})
    if not converted:
        converted = [{"role": "user", "content": "Hello"}]
    # Anthropic requires alternating roles starting with user
    if converted[0]["role"] != "user":
        converted.insert(0, {"role": "user", "content": "(continue)"})
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "messages": converted,
    }
    if system_parts:
        payload["system"] = "\n\n".join(system_parts)
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    url = "https://api.anthropic.com/v1/messages"
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=payload, headers=headers)
        if r.status_code >= 400:
            raise RuntimeError(f"Claude HTTP {r.status_code}: {r.text[:400]}")
        data = r.json()
    try:
        blocks = data.get("content") or []
        texts = [str(b.get("text") or "") for b in blocks if isinstance(b, dict)]
        return "\n".join(t for t in texts if t).strip() or str(data)
    except Exception as exc:
        raise RuntimeError(f"Unexpected Claude payload: {data!r}") from exc


def chat_external(
    provider_id: str,
    messages: list[dict],
    *,
    stored_keys: dict[str, str] | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 1.0,
) -> tuple[str, str, str]:
    """Return (text, display_model, vendor)."""
    meta = LLM_CATALOG.get(provider_id)
    if not meta or meta.get("owned"):
        raise RuntimeError("Not an external provider")
    key = resolve_api_key(provider_id, stored_keys)
    if not key:
        raise RuntimeError(f"No API key for {meta['name']}")
    model = str(meta.get("model") or provider_id)
    style = meta.get("style") or "openai"
    if style == "anthropic":
        text = chat_via_anthropic(
            messages,
            api_key=key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        text = chat_via_openai_compat(
            messages,
            api_key=key,
            base_url=str(meta.get("base_url") or ""),
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    return text, str(meta.get("name") or provider_id), str(meta.get("vendor") or "")


def public_catalog(
    *,
    enabled: dict[str, bool] | None = None,
    keys_set: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    en = enabled or {}
    ks = keys_set or {}
    rows = []
    for pid, meta in LLM_CATALOG.items():
        owned = bool(meta.get("owned"))
        on = True if owned else bool(en.get(pid))
        rows.append(
            {
                "id": pid,
                "name": meta["name"],
                "vendor": meta["vendor"],
                "owned": owned,
                "enabled": on,
                "has_api_key": True if owned else bool(ks.get(pid) or resolve_api_key(pid, {})),
                "model": meta.get("model"),
            }
        )
    return rows
