"""OM-1.0 native backend + no silent fallback tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from om_ai.backends.base import NativeCheckpointError
from om_ai.backends.om_native import OMNativeBackend, _load_project_env
from om_ai.runtime import chat_backend as cb
from om_ai.runtime.engine import CheckpointTokenizerMismatch, LocalLLMEngine
from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint
from om_ai.tokenizer.byte_bpe import ByteBPETokenizer


ROOT = Path(__file__).resolve().parents[1]
TOK_FIXED = ROOT / "artifacts" / "tokenizer-fixed-v3.json"
CFG_LOCAL = ROOT / "configs" / "om-1.0-local.json"


def test_load_tokenizer_single_entry_om_format(tmp_path: Path):
    tok = ByteBPETokenizer.base()
    path = tmp_path / "tok.json"
    tok.save(path)
    loaded = load_tokenizer(path)
    assert loaded.vocab_size == len(loaded.vocab)
    assert loaded.pad_id == 0
    assert loaded.bos_id is not None
    assert loaded.eos_id is not None
    assert loaded.unk_id is not None
    assert hasattr(loaded, "encode_chat")
    assert loaded.fingerprint == tokenizer_fingerprint(path)
    info = loaded.inspect()
    assert info["vocab_size"] == loaded.vocab_size
    assert "pad_id" in info


def test_tokenizer_fingerprint_stable():
    if not TOK_FIXED.is_file():
        pytest.skip("tokenizer-fixed-v3 missing")
    a = tokenizer_fingerprint(TOK_FIXED)
    b = tokenizer_fingerprint(TOK_FIXED)
    assert a == b
    assert len(a) == 64


def test_encode_chat_generation_prompt_ends_assistant_open():
    tok = ByteBPETokenizer.base()
    ids = tok.encode_chat(
        [{"role": "user", "content": "hi"}],
        add_generation_prompt=True,
    )
    assert ids[-1] == tok.assistant_id


def test_degenerate_generation_detects_possessive_collapse():
    from om_ai.runtime.engine import is_degenerate_generation

    garbage = (
        "The Cubs: Mrs and Jerry Dacosta's daughter. During the eve’s1916th "
        "seed couldn’t stop’s daughter’s brother’s lap’s parents’s sister’s mom’s."
    )
    assert is_degenerate_generation(garbage)
    assert not is_degenerate_generation("Hello — I’m OM AI.")


def test_resolve_om_native_forced(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "openai")
    info = cb.resolve_backend(native_ready=False)
    assert info.backend == "om_native"
    assert info.provider == "OM AI"
    assert info.model == "OM-1.0" or "OM" in info.model


def test_om_native_capability_question_uses_model_not_static(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE", "0")

    def native(messages, **_k):
        assert messages
        return "I am OM-1.0 running locally on your checkpoint."

    text, used = cb.chat_reply(
        [{"role": "user", "content": "What can you do as a local OM model?"}],
        native_chat=native,
        native_ready=True,
        local_chat=None,
        local_loaded=False,
    )
    assert "OM-1.0" in text
    assert "Live knowledge" not in text
    assert "Enjoy the videos" not in text
    assert used.backend == "om_native"


def test_om_native_good_morning_bhai_uses_model_not_static(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE", "0")

    def native(messages, **_k):
        return "Good morning! How are you?"

    text, used = cb.chat_reply(
        [{"role": "user", "content": "good morning bhai"}],
        native_chat=native,
        native_ready=True,
        local_chat=None,
        local_loaded=False,
    )
    assert text == "Good morning! How are you?"
    assert "YouTube" not in text
    assert "correct form" not in text.lower()
    assert "Enjoy the videos" not in text
    assert used.backend == "om_native"


def test_om_native_greeting_is_not_web_dump(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE", "0")

    def native(_messages, **_k):
        return "Hello — I'm OM AI."

    text, used = cb.chat_reply(
        [{"role": "user", "content": "good moring how are you"}],
        native_chat=native,
        native_ready=True,
        local_chat=None,
        local_loaded=False,
    )
    assert "OM AI" in text
    assert "Live knowledge" not in text
    assert "howtosayguide" not in text.lower()
    assert used.backend == "om_native"


def test_om_native_garbage_falls_back_to_grounded_live_knowledge(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE", "1")
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE_GROUNDED", "1")

    garbage = (
        "The Cubs: Mrs and Jerry Dacosta's daughter. During the eve’s1916th "
        "seed couldn’t stop’s daughter’s brother’s lap’s parents’s sister’s mom’s."
    )

    def native(_messages, **_k):
        return garbage

    def fake_enrich(messages, **kwargs):
        force = bool(kwargs.get("force"))
        blob = " ".join(str(m.get("content") or "") for m in messages)
        if force or "basketball" in blob.lower() or "cubs" in blob.lower():
            return list(messages), {
                "needs_live": True,
                "llm_used": None,
                "prefer_grounded_reply": True,
                "grounded_reply": "Cubs are an MLB team.",
            }
        return list(messages), {"needs_live": False, "llm_used": None, "prefer_grounded_reply": False}

    monkeypatch.setattr(
        "om_ai.live_knowledge.enrich_messages_for_live_knowledge",
        fake_enrich,
    )

    text, used = cb.chat_reply(
        [{"role": "user", "content": "Who won the Cubs championship?"}],
        native_chat=native,
        native_ready=True,
        local_chat=None,
        local_loaded=False,
    )
    assert "Cubs are an MLB team" in text
    assert used.backend == "om_native"
    assert "couldn’t stop’s" not in text


def test_om_native_no_silent_third_party_fallback(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def boom(*_a, **_k):
        raise AssertionError("OpenAI must not be called in om_native mode")

    monkeypatch.setattr(cb, "chat_via_openai", boom)

    with pytest.raises(NativeCheckpointError, match="native checkpoint is unavailable"):
        cb.chat_reply(
            [{"role": "user", "content": "hi"}],
            native_chat=None,
            native_ready=False,
            local_chat=None,
            local_loaded=False,
        )


def test_om_native_health_unloaded():
    backend = OMNativeBackend()
    h = backend.health()
    assert h["backend"] == "om_native"
    assert h["name"] == "OM-1.0"
    assert h["provider"] == "OM AI"
    assert h["trained"] is False
    info = backend.model_info()
    assert info["trained"] is False
    assert info["name"] == "OM-1.0"


def test_om_native_missing_checkpoint_raises(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OM_MODEL_CHECKPOINT", str(tmp_path / "missing.pt"))
    backend = OMNativeBackend()
    with pytest.raises(NativeCheckpointError, match="OM-1.0 checkpoint unavailable"):
        backend.load(
            str(CFG_LOCAL) if CFG_LOCAL.is_file() else "configs/tiny.json",
            str(TOK_FIXED) if TOK_FIXED.is_file() else "artifacts/tokenizer.json",
            str(tmp_path / "missing.pt"),
            "cpu",
            require_checkpoint=True,
        )


def test_checkpoint_tokenizer_mismatch_rejected(tmp_path: Path):
    import torch
    from om_ai.core.config import ModelConfig
    from om_ai.model import OMTransformer

    if not CFG_LOCAL.is_file() or not TOK_FIXED.is_file():
        pytest.skip("om-1.0-local config or tokenizer missing")

    tok_a = ByteBPETokenizer.base()
    path_a = tmp_path / "tok-a.json"
    tok_a.save(path_a)
    path_b = tmp_path / "tok-b.json"
    # Different merges → different fingerprint
    tok_b = ByteBPETokenizer.train(["hello world hello"], vocab_size=300, min_pair_freq=1)
    tok_b.save(path_b)
    assert tokenizer_fingerprint(path_a) != tokenizer_fingerprint(path_b)

    cfg = ModelConfig.from_json(CFG_LOCAL)
    cfg.vocab_size = len(tok_a.vocab)
    model = OMTransformer(cfg)
    ckpt = tmp_path / "ckpt.pt"
    torch.save(
        {
            "model": model.state_dict(),
            "extra": {"tokenizer_fingerprint": tokenizer_fingerprint(path_a)},
        },
        ckpt,
    )

    eng = LocalLLMEngine()
    with pytest.raises(CheckpointTokenizerMismatch):
        eng.load(str(CFG_LOCAL), str(path_b), str(ckpt), "cpu")


def test_resolve_tokenizer_prefers_vocab_match_over_stale_metadata():
    from om_ai.runtime.engine import resolve_tokenizer_path_for_checkpoint

    if not TOK_FIXED.is_file():
        pytest.skip("tokenizer-fixed-v3 missing")
    prod = ROOT / "artifacts" / "tokenizer-production-65536.json"
    if not prod.is_file():
        pytest.skip("production tokenizer missing")

    chosen = resolve_tokenizer_path_for_checkpoint(
        str(TOK_FIXED),
        65536,
        {"tokenizer_path": "artifacts/tokenizer-fixed-v3.json"},
    )
    assert Path(chosen).resolve() == prod.resolve()


def test_checkpoint_vocab_mismatch_autoselects_extra_tokenizer(tmp_path: Path):
    import torch
    from om_ai.core.config import ModelConfig
    from om_ai.model import OMTransformer

    if not CFG_LOCAL.is_file():
        pytest.skip("om-1.0-local config missing")

    tok_small = ByteBPETokenizer.base()
    path_small = tmp_path / "tok-small.json"
    tok_small.save(path_small)

    tok_wide = ByteBPETokenizer.train(
        ["hello world hello om ai native checkpoint"] * 20,
        vocab_size=max(len(tok_small.vocab) + 40, 320),
        min_pair_freq=1,
    )
    path_wide = tmp_path / "tok-wide.json"
    tok_wide.save(path_wide)
    assert len(tok_wide.vocab) != len(tok_small.vocab)

    cfg = ModelConfig.from_json(CFG_LOCAL)
    cfg.vocab_size = len(tok_wide.vocab)
    model = OMTransformer(cfg)
    ckpt = tmp_path / "ckpt.pt"
    torch.save(
        {
            "model": model.state_dict(),
            "extra": {
                "tokenizer_path": str(path_wide),
                "tokenizer_fingerprint": tokenizer_fingerprint(path_small),
            },
        },
        ckpt,
    )

    eng = LocalLLMEngine()
    info = eng.load(str(CFG_LOCAL), str(path_small), str(ckpt), "cpu")
    assert eng.model is not None
    assert eng.model.cfg.vocab_size == len(tok_wide.vocab)
    assert info["tokenizer"]["vocab_size"] == len(tok_wide.vocab)


def test_project_env_loads_from_repo_root_and_preserves_shell_values(tmp_path: Path, monkeypatch):
    import os

    env_file = tmp_path / ".env"
    env_file.write_text(
        "OM_MODEL_CONFIG=configs/from-env.json\n"
        "OM_MODEL_TOKENIZER=artifacts/from-env-tokenizer.json\n"
        "OM_MODEL_CHECKPOINT=artifacts/from-env-checkpoint/latest.pt\n",
        encoding="utf-8",
    )
    for key in ("OM_MODEL_CONFIG", "OM_MODEL_TOKENIZER", "OM_MODEL_CHECKPOINT"):
        monkeypatch.delenv(key, raising=False)

    _load_project_env(tmp_path)
    assert os.environ["OM_MODEL_CONFIG"] == "configs/from-env.json"
    assert os.environ["OM_MODEL_TOKENIZER"] == "artifacts/from-env-tokenizer.json"
    assert os.environ["OM_MODEL_CHECKPOINT"] == "artifacts/from-env-checkpoint/latest.pt"

    monkeypatch.setenv("OM_MODEL_CHECKPOINT", "/explicit/shell/checkpoint.pt")
    _load_project_env(tmp_path)
    assert os.environ["OM_MODEL_CHECKPOINT"] == "/explicit/shell/checkpoint.pt"


def test_om_native_garbage_does_not_become_canned_answer(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_NATIVE_MODEL_FIRST", "1")
    monkeypatch.setenv("OM_LIVE_KNOWLEDGE", "0")

    def native(_messages, **_kwargs):
        return "C_yAI*uing att(;e potoentPEZec random token soup"

    text, used = cb.chat_reply(
        [{"role": "user", "content": "Explain how Python functions work."}],
        native_chat=native,
        native_ready=True,
        local_chat=None,
        local_loaded=False,
    )
    assert used.backend == "om_native"
    assert "could not produce a reliable answer" in text.lower()
    assert "how can i help" not in text.lower()
