"""Companion runtime configuration from env."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _on(name: str, default: str = "1") -> bool:
    return (os.getenv(name) or default).strip().lower() not in {"0", "false", "no", "off"}


@dataclass
class CompanionConfig:
    enabled: bool = True
    wake_word_enabled: bool = True
    wake_word: str = "hey om"
    stt_provider: str = "auto"
    tts_provider: str = "auto"
    avatar_enabled: bool = True
    memory_enabled: bool = True
    actions_enabled: bool = True
    always_ready: bool = True
    bind_host: str = "127.0.0.1"
    bind_port: int = 8765
    text_only: bool = False
    no_avatar: bool = False

    @classmethod
    def from_env(cls, **overrides) -> "CompanionConfig":
        cfg = cls(
            enabled=_on("OM_COMPANION_ENABLED", "1"),
            wake_word_enabled=_on("OM_COMPANION_WAKE_WORD_ENABLED", "1"),
            wake_word=(os.getenv("OM_COMPANION_WAKE_WORD") or "hey om").strip().lower(),
            stt_provider=(os.getenv("OM_COMPANION_STT_PROVIDER") or "auto").strip(),
            tts_provider=(os.getenv("OM_COMPANION_TTS_PROVIDER") or "auto").strip(),
            avatar_enabled=_on("OM_COMPANION_AVATAR_ENABLED", "1"),
            memory_enabled=_on("OM_COMPANION_MEMORY_ENABLED", "1"),
            actions_enabled=_on("OM_COMPANION_ACTIONS_ENABLED", "1"),
            always_ready=_on("OM_COMPANION_ALWAYS_READY", "1"),
            bind_host=(os.getenv("OM_COMPANION_BIND_HOST") or "127.0.0.1").strip(),
            bind_port=int(os.getenv("OM_COMPANION_BIND_PORT") or os.getenv("PORT") or "8765"),
        )
        for k, v in overrides.items():
            if hasattr(cfg, k) and v is not None:
                setattr(cfg, k, v)
        if cfg.text_only:
            cfg.wake_word_enabled = False
        return cfg
