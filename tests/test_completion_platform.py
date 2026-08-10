from __future__ import annotations

from pathlib import Path

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer, RMSNorm
from om_ai.security import SSRFGuard, RBAC, RateLimiter
from om_ai.security.ssrf import SSRFError
from om_ai.checkpoint import save_bundle, verify_integrity
from om_ai.knowledge import PersistentKnowledgeBase
from om_ai.memory import SQLiteMemoryStore
from om_ai.agents import AgentOrchestrator
from om_ai.actions import SafeShellTool, KnowledgeSearchTool
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.training.ppo import Rollout, compute_advantages
from om_ai.discovery import ProjectDiscovery


def test_rmsnorm_and_generation_controls():
    cfg = ModelConfig(vocab_size=128, max_seq_len=32, n_layers=1, n_heads=4, d_model=32, d_ff=64, use_rmsnorm=True)
    m = OMTransformer(cfg)
    assert isinstance(m.final_norm, RMSNorm)
    x = torch.randint(0, 128, (1, 4))
    out = m.generate(x, max_new_tokens=3, temperature=0.7, top_k=10, top_p=0.9, repetition_penalty=1.1)
    assert out.shape[1] >= 4


def test_ssrf_blocks_localhost():
    g = SSRFGuard()
    try:
        g.validate_url("http://127.0.0.1/secret")
        raised = False
    except (ValueError, SSRFError):
        raised = True
    assert raised


def test_rbac_matrix():
    r = RBAC()
    assert r.can("admin", "model.load")
    assert not r.can("viewer", "agent.run")


def test_rate_limiter():
    lim = RateLimiter(max_requests=2, window_seconds=60)
    lim.check("k")
    lim.check("k")
    try:
        lim.check("k")
        ok = True
    except Exception:
        ok = False
    assert not ok


def test_persistent_rag_tenant_isolation(tmp_path: Path):
    kb = PersistentKnowledgeBase(str(tmp_path / "kb.sqlite3"))
    kb.add("d1", "OM AI private brain alpha", tenant_id="t1")
    kb.add("d2", "other tenant secret beta", tenant_id="t2")
    hits = kb.search("private brain", "t1", k=5)
    assert hits
    secret_hits = kb.search("secret beta", "t1", k=5)
    assert not any("secret beta" in h.text for h in secret_hits)


def test_memory_relevance(tmp_path: Path):
    mem = SQLiteMemoryStore(str(tmp_path / "mem.sqlite3"))
    mem.add("t", "u", "User likes dark mode UI", kind="preference")
    mem.add("t", "u", "Random weather note", kind="conversation")
    rel = mem.get_relevant("dark mode preference", "t", "u", limit=2)
    assert rel
    assert any("dark" in m.content.lower() for m in rel)


def test_agent_registers_knowledge_tool(tmp_path: Path):
    kb = PersistentKnowledgeBase(str(tmp_path / "kb.sqlite3"))
    kb.add("x", "findable document about transformers", tenant_id="default")
    agent = AgentOrchestrator()
    agent.register_tool(KnowledgeSearchTool(kb))
    agent.register_tool(SafeShellTool(["echo"]))
    out = agent.execute_goal("search for transformers", max_steps=4)
    assert "plan" in out


def test_checkpoint_bundle(tmp_path: Path):
    cfg = ModelConfig(vocab_size=64, max_seq_len=16, n_layers=1, n_heads=2, n_kv_heads=2, d_model=16, d_ff=32)
    model = OMTransformer(cfg)
    tok = ByteBPETokenizer.base()
    tok_path = tmp_path / "tok.json"
    tok.save(tok_path)
    root = save_bundle(
        tmp_path,
        model.state_dict(),
        cfg.to_dict(),
        str(tok_path),
        model_name="OM-LM-test",
        training_state={"step": 1},
        provenance={"note": "unit"},
        trained=True,
    )
    assert root.exists()
    assert verify_integrity(tmp_path, model_name="OM-LM-test")


def test_ppo_advantages():
    rollout = Rollout(
        prompt_ids=[1, 2],
        response_ids=[3, 4, 5],
        logprobs=[-0.1, -0.2, -0.3],
        ref_logprobs=[-0.1, -0.2, -0.25],
        values=[0.5, 0.4, 0.3],
        reward=1.0,
    )
    out = compute_advantages(rollout, gamma=0.99, lam=0.95)
    assert out.advantages is not None
    assert len(out.advantages) == 3


def test_project_discovery():
    disc = ProjectDiscovery(".")
    result = disc.scan()
    data = result.to_dict() if hasattr(result, "to_dict") else result
    assert isinstance(data, dict)


def test_tokenizer_chat_tokens():
    tok = ByteBPETokenizer.base()
    assert "<user>" in tok.vocab
    ids = tok.encode_chat(
        [{"role": "user", "content": "hi"}],
        add_generation_prompt=True,
    )
    assert isinstance(ids, list) and len(ids) > 0
    assert ids[0] == tok.bos_id
    assert ids[-1] == tok.assistant_id
    assert tok.eos_id not in ids
