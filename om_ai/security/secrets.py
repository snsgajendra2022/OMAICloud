"""Secret management and redaction utilities for OM AI.

SecretStore reads secrets from environment variables only, never from .env
files, and provides a redact() function to mask sensitive values in logs.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns to detect and redact in text
# ---------------------------------------------------------------------------

_REDACT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # api_key=…  / api-key=…  / apikey=…
    (re.compile(r"(api[_\-]?key\s*[=:]\s*)([^\s,&\"']{4,})", re.IGNORECASE), r"\1[REDACTED]"),
    # secret=…
    (re.compile(r"(secret\s*[=:]\s*)([^\s,&\"']{4,})", re.IGNORECASE), r"\1[REDACTED]"),
    # password=…  / passwd=…
    (re.compile(r"(pass(?:word|wd)?\s*[=:]\s*)([^\s,&\"']{4,})", re.IGNORECASE), r"\1[REDACTED]"),
    # token=…
    (re.compile(r"(token\s*[=:]\s*)([^\s,&\"']{4,})", re.IGNORECASE), r"\1[REDACTED]"),
    # Bearer <token>
    (re.compile(r"(Bearer\s+)([A-Za-z0-9\-._~+/]{16,})", re.IGNORECASE), r"\1[REDACTED]"),
    # sk-… (OpenAI style secret keys)
    (re.compile(r"\bsk-[A-Za-z0-9]{10,}\b"), "[REDACTED]"),
    # Generic hex secrets ≥ 32 chars after = or :
    (re.compile(r"([=:]\s*)([0-9a-fA-F]{32,})\b"), r"\1[REDACTED]"),
    # X-OM-API-Key header value in logs
    (re.compile(r"(X-OM-API-Key\s*[=:]\s*)([^\s,&\"']{6,})", re.IGNORECASE), r"\1[REDACTED]"),
]

# Environment variable names whose values should never be revealed
_SENSITIVE_ENV_PREFIXES: tuple[str, ...] = (
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "TOKEN",
    "API_KEY",
    "APIKEY",
    "SK_",
    "OM_AI_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "HUGGING_FACE_HUB_TOKEN",
    "HF_TOKEN",
    "AWS_SECRET",
    "AZURE_CLIENT_SECRET",
)

# File-path keys that could be .env files (never read these)
_ENV_FILE_KEYS: frozenset[str] = frozenset(
    {
        "OM_AI_API_KEYS_FILE",  # allowed (JSON map, not .env)
    }
)

# Detect .env file paths
_ENV_FILE_RE = re.compile(r"(^|/)\.env(\.[a-z]+)?$", re.IGNORECASE)


class SecretStore:
    """Read-only access to environment-sourced secrets.

    Rules:
    - Reads from ``os.environ`` only.
    - Will never return a value whose source path matches ``.env*`` file.
    - Logs a warning if the caller requests a sensitive key.
    - Provides ``redact()`` to mask secrets in log output.
    """

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Return the value of environment variable *name*.

        Returns *default* if not set. Raises RuntimeError if the variable
        looks like it points to a .env file (use OM_AI_API_KEYS_FILE for JSON
        key maps, which is a safe format).
        """
        value = os.environ.get(name)

        if value is None:
            return default

        # Protect against a variable that is *itself* a .env file path being
        # returned when the caller didn't intend to load a file
        if name not in _ENV_FILE_KEYS and _ENV_FILE_RE.search(value):
            logger.warning(
                "SecretStore.get('%s') value looks like a .env file path – "
                "refusing to return it to prevent accidental secret disclosure.",
                name,
            )
            return default

        name_upper = name.upper()
        if any(name_upper.startswith(prefix) for prefix in _SENSITIVE_ENV_PREFIXES):
            logger.debug("SecretStore: sensitive key '%s' accessed.", name)

        return value

    def require(self, name: str) -> str:
        """Like ``get()`` but raises KeyError if the key is absent."""
        value = self.get(name)
        if value is None:
            raise KeyError(f"Required secret '{name}' is not set in environment.")
        return value

    def is_set(self, name: str) -> bool:
        """Return True if *name* is present in the environment."""
        return os.environ.get(name) is not None

    @staticmethod
    def redact(text: str) -> str:
        """Return *text* with known secret patterns masked as ``[REDACTED]``."""
        result = text
        for pattern, replacement in _REDACT_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def env_snapshot(self, *, include_sensitive: bool = False) -> dict[str, str]:
        """Return a copy of the current environment with sensitive values redacted.

        Useful for including in diagnostic reports without leaking secrets.
        Set *include_sensitive=True* only in fully trusted internal contexts.
        """
        snapshot: dict[str, str] = {}
        for key, value in os.environ.items():
            key_upper = key.upper()
            if not include_sensitive and any(
                key_upper.startswith(p) for p in _SENSITIVE_ENV_PREFIXES
            ):
                snapshot[key] = "[REDACTED]"
            else:
                snapshot[key] = value
        return snapshot
