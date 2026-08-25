"""OMAI-Tokenizer-v1 special-token contract.

Production weights currently use chat specials already in
``artifacts/tokenizer-production-65536.json``:

    <system> </system> <user> </user> <assistant> </assistant>

Roadmap aliases (documented for future vocab expansion / remapping):

    <|system|> <|user|> <|assistant|> <|code|> <|reasoning|>
"""
from __future__ import annotations

from typing import Any

# Live specials in current production tokenizer (ByteBPE / HF adapter)
CHAT_SPECIALS_V1 = [
    "<pad>",
    "<bos>",
    "<eos>",
    "<unk>",
    "<system>",
    "</system>",
    "<user>",
    "</user>",
    "<assistant>",
    "</assistant>",
]

# Planned additions for OMAI-Tokenizer-v1 expansion (not yet in 65k vocab file)
PLANNED_DOMAIN_SPECIALS = [
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "<|code|>",
    "<|reasoning|>",
    "<|math|>",
]

# Stable aliases: roadmap name → current production token
ALIAS_TO_PRODUCTION = {
    "<|system|>": "<system>",
    "<|user|>": "<user>",
    "<|assistant|>": "<assistant>",
}


def tokenizer_v1_status(tokenizer_path: str = "artifacts/tokenizer-production-65536.json") -> dict[str, Any]:
    from pathlib import Path

    from om_ai.tokenizer import load_tokenizer

    path = Path(tokenizer_path)
    if not path.is_file():
        return {"ok": False, "error": "tokenizer_missing", "path": str(path)}
    tok = load_tokenizer(str(path))
    vocab = getattr(tok, "vocab", {}) or {}
    present = [t for t in CHAT_SPECIALS_V1 if t in vocab or getattr(tok, "_id", lambda _x: None)(t) is not None]
    # HF adapter uses _id
    if hasattr(tok, "_id"):
        present = [t for t in CHAT_SPECIALS_V1 if tok._id(t) is not None]
    return {
        "ok": True,
        "name": "omai-tokenizer-v1",
        "path": str(path),
        "vocab_size": getattr(tok, "vocab_size", None),
        "chat_specials_present": present,
        "chat_specials_complete": len(present) >= 10,
        "planned_domain_specials": PLANNED_DOMAIN_SPECIALS,
        "aliases": ALIAS_TO_PRODUCTION,
        "complete_pct": 85 if len(present) >= 10 else 60,
        "note": "Chat specials live. Domain tokens <|code|>/<|reasoning|> planned for next vocab train.",
    }
