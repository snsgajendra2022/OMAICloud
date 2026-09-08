"""Tests for self-contained OM BPE tokenizer + knowledge aggregation."""
from __future__ import annotations

from om_ai.training.om_tokenizer import OMTokenizer
from om_ai.training.local_knowledge import SEED_KNOWLEDGE, aggregate_local_docs


def test_om_tokenizer_bpe_roundtrip():
    tok = OMTokenizer(vocab_size=200)
    tok.train_tokenizer(SEED_KNOWLEDGE * 3)
    assert "<|user|>" in tok.encoder
    assert "<|assistant|>" in tok.encoder
    ids = tok.encode("<|user|> Hello <|assistant|> Hi there")
    assert tok.user_id in ids
    text = tok.decode(ids)
    assert "Hello" in text or "Hi" in text or "<|user|>" in text


def test_aggregate_local_docs(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    (src / "note.md").write_text("Gravity pulls objects together on Earth.\n" * 5, encoding="utf-8")
    out = tmp_path / "knowledge.txt"
    result = aggregate_local_docs([src], out, max_files=10, include_seed=True)
    assert result["files"] >= 1
    body = out.read_text(encoding="utf-8")
    assert "<|user|>" in body
    assert "stressed" in body or "Gravity" in body
