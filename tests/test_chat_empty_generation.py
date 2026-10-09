"""Empty / oversized-system chat generation hardening."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from om_ai.runtime.chat_backend import with_runtime_date_context
from om_ai.runtime.engine import (
    EMPTY_GENERATION_FALLBACK,
    fit_messages_to_context,
    usable_generation_text,
)
from om_ai.tokenizer import load_tokenizer


ROOT = Path(__file__).resolve().parents[1]
TOK_FIXED = ROOT / "artifacts" / "tokenizer-fixed-v3.json"


def test_usable_generation_text_rejects_empty_and_garbage():
    assert usable_generation_text("") == ""
    assert usable_generation_text("   ") == ""
    assert usable_generation_text("\x00\x01\x02") == ""
    assert usable_generation_text("Hello — I'm OM AI.") == "Hello — I'm OM AI."


def test_degenerate_generation_rejects_token_soup_but_keeps_normal_text():
    from om_ai.runtime.engine import is_degenerate_generation

    garbage = "C_yAI*uing andev9roal R#1e p atten att(;e potoentPEZec att))k/Uing andAIrEPu"
    assert is_degenerate_generation(garbage)
    assert not is_degenerate_generation("The sky appears blue because air scatters blue light more strongly.")
    assert not is_degenerate_generation("Hello — I'm OM AI.")


def test_fit_messages_drops_oversized_system_for_tiny_context():
    if not TOK_FIXED.is_file():
        pytest.skip("tokenizer-fixed-v3 missing")
    tok = load_tokenizer(TOK_FIXED)
    msgs = with_runtime_date_context(
        [{"role": "user", "content": "hello how are you"}],
        today=date(2026, 8, 13),
    )
    # Simulate OM-1.0-local max_seq_len=128.
    fitted = fit_messages_to_context(msgs, tok, 128, today=date(2026, 8, 13))
    ids = tok.encode_chat(fitted, add_generation_prompt=True, add_eos=False)
    assert len(ids) <= 128
    assert ids[-1] == tok.assistant_id
    assert all(m["role"] != "system" for m in fitted)
    # User turn must survive fitting.
    blob = tok.decode(ids)
    assert "hello how are you" in blob


def test_empty_fallback_constant():
    assert "no text" in EMPTY_GENERATION_FALLBACK.lower()
