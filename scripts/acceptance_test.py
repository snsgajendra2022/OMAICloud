#!/usr/bin/env python3
"""End-to-end acceptance test for OM AI software platform (tiny scale).

Exits non-zero if any core stage fails.
Does NOT claim frontier intelligence — only verifies the software pipeline.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd or ROOT)


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="om-ai-accept-"))
    try:
        data = work / "corpus.txt"
        data.write_text(
            "OM AI is a private operating brain.\n"
            "Licensed sample text for tokenizer and pretraining smoke.\n"
            "Agents use tools, memory, and retrieval.\n"
            "DPO prefers clearer answers over vague ones.\n"
        )
        tok = work / "tokenizer.json"
        cfg = ROOT / "configs" / "tiny.json"
        ckpt_dir = work / "pretrain"
        sft_data = work / "sft.jsonl"
        sft_data.write_text(
            json.dumps({"prompt": "What is OM AI?", "response": "A private AI platform.", "system": "Be concise."})
            + "\n"
        )
        pref = work / "pref.jsonl"
        pref.write_text(
            json.dumps({"prompt": "Say hello", "chosen": "Hello, how can I help?", "rejected": "idk"})
            + "\n"
        )
        sft_dir = work / "sft"
        dpo_dir = work / "dpo"
        report = work / "eval.json"
        kb_db = work / "kb.sqlite3"
        mem_db = work / "mem.sqlite3"

        run([str(PY), "-m", "om_ai.cli", "tokenizer", "train", "--input", str(data), "--output", str(tok), "--vocab-size", "400"])
        run([str(PY), "-m", "om_ai.cli", "model-info", "--config", str(cfg), "--tokenizer", str(tok)])
        run([
            str(PY), "-m", "om_ai.cli", "pretrain",
            "--config", str(cfg), "--data", str(data), "--tokenizer", str(tok),
            "--steps", "3", "--batch-size", "1", "--output", str(ckpt_dir),
            "--checkpoint-every", "3", "--log-every", "1",
        ])
        pre_ckpt = ckpt_dir / "latest.pt"
        assert pre_ckpt.exists(), "pretrain checkpoint missing"
        run([
            str(PY), "-m", "om_ai.cli", "sft",
            "--config", str(cfg), "--data", str(sft_data), "--tokenizer", str(tok),
            "--checkpoint", str(pre_ckpt), "--steps", "2", "--batch-size", "1",
            "--output", str(sft_dir), "--checkpoint-every", "2",
        ])
        sft_ckpt = sft_dir / "latest.pt"
        run([
            str(PY), "-m", "om_ai.cli", "dpo",
            "--config", str(cfg), "--data", str(pref), "--tokenizer", str(tok),
            "--checkpoint", str(sft_ckpt), "--steps", "2", "--batch-size", "1",
            "--output", str(dpo_dir),
        ])
        dpo_ckpt = dpo_dir / "latest.pt"
        run([
            str(PY), "-m", "om_ai.cli", "benchmark",
            "--config", str(cfg), "--tokenizer", str(tok), "--checkpoint", str(dpo_ckpt),
            "--benchmark", str(ROOT / "benchmarks" / "core.jsonl"),
            "--report", str(report), "--max-new-tokens", "8",
        ])
        assert report.exists()

        # Memory + RAG + agent wiring smoke (in-process)
        sys.path.insert(0, str(ROOT))
        from om_ai.knowledge import PersistentKnowledgeBase
        from om_ai.memory import SQLiteMemoryStore
        from om_ai.agents import AgentOrchestrator
        from om_ai.actions import KnowledgeSearchTool, SafeShellTool
        from om_ai.runtime import LocalLLMEngine
        from om_ai.checkpoint import save_bundle, verify_integrity
        from om_ai.core.config import ModelConfig
        from om_ai.model import OMTransformer
        from om_ai.tokenizer import ByteBPETokenizer
        import torch

        kb = PersistentKnowledgeBase(str(kb_db))
        kb.add("doc1", "OM AI uses licensed corpora and local checkpoints.", tenant_id="default")
        mem = SQLiteMemoryStore(str(mem_db))
        mem.add("default", "user", "User prefers concise answers", kind="preference")
        eng = LocalLLMEngine()
        eng.load(str(cfg), str(tok), str(dpo_ckpt))
        ctx = kb.build_context("licensed corpora", tenant_id="default", k=2)
        _ = eng.generate_with_context("Summarize.", rag_context=ctx.get("context_text", ""), max_new_tokens=8)
        agent = AgentOrchestrator(llm_engine=eng, knowledge_base=kb, memory_store=mem)
        agent.register_tool(KnowledgeSearchTool(kb))
        agent.register_tool(SafeShellTool(["echo"]))
        result = agent.execute_goal("search licensed corpora", max_steps=4)
        assert "plan" in result

        tokenizer = ByteBPETokenizer.load(tok)
        model_cfg = ModelConfig.from_json(cfg)
        model_cfg.vocab_size = len(tokenizer.vocab)
        model = OMTransformer(model_cfg)
        model.load_state_dict(torch.load(dpo_ckpt, map_location="cpu", weights_only=False)["model"])
        bundle = save_bundle(
            work,
            model.state_dict(),
            model.cfg.to_dict(),
            str(tok),
            model_name="OM-LM-accept",
            training_state={"stage": "dpo", "steps": 2},
            evaluation=json.loads(report.read_text()),
            provenance={"pipeline": "acceptance"},
            trained=True,
        )
        assert verify_integrity(work, model_name="OM-LM-accept")

        print(json.dumps({
            "acceptance": "PASS",
            "work_dir": str(work),
            "checkpoint": str(dpo_ckpt),
            "bundle": str(bundle),
            "note": "Tiny smoke only — not a capability claim.",
        }, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"acceptance": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    finally:
        # keep artifacts on failure for debugging; delete on success
        if "--keep" not in sys.argv:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
