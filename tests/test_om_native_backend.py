"""OM-1.0 native backend + no silent fallback tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from om_ai.backends.base import NativeCheckpointError
from om_ai.backends.om_native import OMNativeBackend
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


def test_resolve_om_native_forced(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OM_AI_CHAT_BACKEND", "openai")
    info = cb.resolve_backend(native_ready=False)
    assert info.backend == "om_native"
    assert info.provider == "OM AI"
    assert info.model == "OM-1.0" or "OM" in info.model


def test_om_native_no_silent_third_party_fallback(monkeypatch):
    monkeypatch.setenv("OM_MODEL_PROVIDER", "om_native")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def boom(*_a, **_k):
        raise AssertionError("OpenAI must not be called in om_native mode")

    monkeypatch.setattr(cb, "chat_via_openai", boom)

    with pytest.raises(NativeCheckpointError, match="OM-1.0 checkpoint unavailable"):
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
