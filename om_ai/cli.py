from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer, load_tokenizer
from om_ai.training import (
    Trainer,
    TrainingConfig,
    build_dataset,
    SFTDataset,
    SFTConfig,
    SFTTrainer,
    PreferenceDataset,
    DPOConfig,
    DPOTrainer,
    RewardModel,
    RewardConfig,
    RewardTrainer,
    PPOConfig,
    PPOTrainer,
    RolloutBuffer,
)
from om_ai.training.ppo import Rollout, ValueHead, compute_advantages
from om_ai.eval import EvaluationHarness, BenchmarkRunner
from om_ai.runtime import LocalLLMEngine
from om_ai.continuous import FeedbackStore, build_sft_replay, build_preference_replay
from om_ai.corpus import CorpusService
from om_ai.registry import ModelRegistry
from om_ai.checkpoint import save_bundle, verify_integrity
from om_ai.discovery import ProjectDiscovery


def load_model(config_path, tokenizer_path, checkpoint=None, device=None):
    """Load OMTransformer sized to the checkpoint embedding table (not just tokenizer len).

    Chat SFT/DPO checkpoints were trained with vocab_size=65536 while some local
    tokenizers are smaller (e.g. 340). The model must match the checkpoint; unused
    embedding rows are fine as long as encoded ids stay in-range.
    """
    from om_ai.training.production_pipeline import pick_training_device

    cfg = ModelConfig.from_json(config_path)
    tok_path = Path(tokenizer_path) if tokenizer_path else None
    tok = load_tokenizer(str(tok_path) if tok_path else tokenizer_path)
    cfg.vocab_size = max(int(cfg.vocab_size or 0), len(tok.vocab))
    dev = torch.device(device or pick_training_device())

    state = None
    if checkpoint:
        ck = torch.load(checkpoint, map_location=dev, weights_only=False)
        state = ck.get("model", ck)
        emb = state.get("token_embedding.weight") if isinstance(state, dict) else None
        if emb is not None:
            ck_vocab = int(emb.shape[0])
            if ck_vocab != cfg.vocab_size:
                print(
                    json.dumps(
                        {
                            "warning": "vocab_size_aligned_to_checkpoint",
                            "tokenizer_vocab": len(tok.vocab),
                            "config_vocab": cfg.vocab_size,
                            "checkpoint_vocab": ck_vocab,
                            "tokenizer": str(tok_path or tokenizer_path),
                            "checkpoint": str(checkpoint),
                        }
                    ),
                    flush=True,
                )
                cfg.vocab_size = ck_vocab
            # Prefer a tokenizer whose vocab matches the checkpoint embedding table.
            if len(tok.vocab) != ck_vocab:
                alt = Path("artifacts/tokenizer-production-65536.json")
                if ck_vocab >= 60000 and alt.is_file():
                    tok = load_tokenizer(str(alt))
                    print(
                        json.dumps(
                            {
                                "tokenizer_switched": str(alt),
                                "tokenizer_vocab": len(tok.vocab),
                                "checkpoint_vocab": ck_vocab,
                                "reason": "match_checkpoint_embedding",
                            }
                        ),
                        flush=True,
                    )
                else:
                    print(
                        json.dumps(
                            {
                                "warning": "tokenizer_vocab_mismatch",
                                "tokenizer_vocab": len(tok.vocab),
                                "checkpoint_vocab": ck_vocab,
                                "hint": "Pass --tokenizer artifacts/tokenizer-production-65536.json",
                            }
                        ),
                        flush=True,
                    )

    model = OMTransformer(cfg).to(dev)
    if state is not None:
        model.load_state_dict(state)
    return cfg, tok, model, dev


def model_info(args):
    # Native OM-1.0 summary when --config omitted (or --native).
    if getattr(args, "native", False) or not getattr(args, "config", None):
        from om_ai.backends.om_native import default_native_paths, pick_device
        from om_ai.backends.om_registry import load_registry_metadata, sync_om10_registry
        from om_ai.tokenizer import tokenizer_fingerprint

        paths = default_native_paths()
        try:
            meta = sync_om10_registry(
                checkpoint=paths.get("checkpoint") or None,
                tokenizer=paths.get("tokenizer"),
                config=paths.get("config"),
                stamp_checkpoint=True,
            )
        except Exception:
            meta = load_registry_metadata() or {}
        tok_path = paths.get("tokenizer") or ""
        tok_ok = bool(tok_path and Path(tok_path).is_file())
        ckpt_path = paths.get("checkpoint") or meta.get("checkpoint") or ""
        ckpt_ok = bool(ckpt_path and Path(str(ckpt_path)).is_file())
        try:
            device = str(pick_device(paths.get("device") or None))
        except Exception:
            device = "cpu"
        human = {
            "Name": "OM-1.0",
            "Provider": "OM AI",
            "Backend": "OM Native",
            "Checkpoint": "verified" if ckpt_ok else "missing",
            "Tokenizer": "verified" if tok_ok else "missing",
            "Device": device.upper() if device in {"cpu", "mps", "cuda"} else device,
            "checkpoint_path": str(ckpt_path) if ckpt_path else None,
            "tokenizer_path": tok_path or None,
            "tokenizer_sha256": (
                tokenizer_fingerprint(tok_path) if tok_ok else meta.get("tokenizer_sha256")
            ),
            "steps": meta.get("steps"),
            "parameters": meta.get("parameters"),
            "trained": bool(meta.get("trained") and ckpt_ok),
            "not_70b": True,
            "honesty": "Local OM-1.0 checkpoint; not production frontier intelligence.",
        }
        print(json.dumps(human, indent=2))
        return

    cfg = ModelConfig.from_json(args.config)
    estimate = cfg.parameter_estimate()
    payload = {
        "config": args.config,
        "parameter_estimate": estimate,
        "parameter_estimate_billions": round(estimate / 1e9, 4),
        "d_model": cfg.d_model,
        "n_layers": cfg.n_layers,
        "n_heads": cfg.n_heads,
        "n_kv_heads": cfg.n_kv_heads,
        "max_seq_len": cfg.max_seq_len,
        "vocab_size": cfg.vocab_size,
        "use_rmsnorm": cfg.use_rmsnorm,
        "gradient_checkpointing": cfg.gradient_checkpointing,
        "trained_weights": False,
        "note": "Estimate from architecture JSON. Instantiate with matching vocab for exact count.",
    }
    if args.tokenizer:
        tok = load_tokenizer(args.tokenizer)
        cfg.vocab_size = len(tok.vocab)
        model = OMTransformer(cfg)
        payload["exact_parameters"] = model.exact_parameter_count()
        payload["trainable_parameters"] = model.trainable_parameter_count()
        payload["vocab_size"] = cfg.vocab_size
        payload["parameter_estimate"] = cfg.parameter_estimate()
    print(json.dumps(payload, indent=2))


def tokenizer_train(args):
    from om_ai.data import DatasetPipeline

    records = DatasetPipeline().process(DatasetPipeline.load(args.input))
    texts = [r.text for r in records]
    tok = ByteBPETokenizer.train(texts, vocab_size=args.vocab_size, min_pair_freq=args.min_pair_freq)
    tok.save(args.output)
    print(json.dumps({"output": args.output, "vocab_size": len(tok.vocab), "merges": len(tok.merges)}))


def tokenizer_inspect(args):
    tok = load_tokenizer(args.tokenizer)
    print(json.dumps(tok.inspect() if hasattr(tok, "inspect") else {
        "vocab_size": len(tok.vocab), "merges": len(tok.merges)
    }, indent=2))


def tokenizer_encode(args):
    tok = load_tokenizer(args.tokenizer)
    ids = tok.encode(args.text, add_bos=args.bos, add_eos=args.eos)
    print(json.dumps({"ids": ids, "n_tokens": len(ids)}))


def tokenizer_decode(args):
    tok = load_tokenizer(args.tokenizer)
    ids = json.loads(args.ids) if args.ids.strip().startswith("[") else [int(x) for x in args.ids.split(",")]
    print(json.dumps({"text": tok.decode(ids)}))


def train(args):
    cfg, tok, model, _ = load_model(args.config, args.tokenizer, None, args.device)
    if args.gradient_checkpointing:
        model.set_gradient_checkpointing(True)
    tc = TrainingConfig(
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        output_dir=args.output,
        checkpoint_every=args.checkpoint_every,
        log_every=args.log_every,
        grad_accum_steps=args.grad_accum,
        precision=args.precision,
    )
    trainer = Trainer(model, tc, device=args.device)
    if args.resume:
        trainer.load_checkpoint(args.resume)
    ds = build_dataset(args.data, tok, cfg.max_seq_len)
    print(json.dumps({"device": str(trainer.device), "parameters": model.exact_parameter_count(), "dataset_blocks": len(ds)}))
    print(json.dumps(trainer.train(ds), indent=2))


def train_om_cmd(args):
    """Run root train_om.py (scratch → MPS training) with the same flags."""
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "train_om.py"
    spec = importlib.util.spec_from_file_location("om_train_om_script", script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {script}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    argv: list[str] = ["--mode", args.mode]
    if args.device:
        argv.extend(["--device", args.device])
    if args.data:
        argv.extend(["--data", args.data])
    if args.config:
        argv.extend(["--config", args.config])
    if args.tokenizer:
        argv.extend(["--tokenizer", args.tokenizer])
    if args.output:
        argv.extend(["--output", args.output])
    argv.extend(
        [
            "--batch-size",
            str(args.batch_size),
            "--block-size",
            str(args.block_size),
            "--max-iters",
            str(args.max_iters),
            "--lr",
            str(args.lr),
            "--eval-interval",
            str(args.eval_interval),
            "--vocab-size",
            str(getattr(args, "vocab_size", 2000)),
        ]
    )
    if getattr(args, "build_knowledge", None) is not None:
        argv.append("--build-knowledge")
        argv.extend(list(args.build_knowledge or []))
        argv.extend(["--knowledge-out", getattr(args, "knowledge_out", "knowledge.txt")])
        if getattr(args, "train_after_build", False):
            argv.append("--train-after-build")
    raise SystemExit(mod.main(argv))


def om_core_cmd(args):
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "om_core.py"
    spec = importlib.util.spec_from_file_location("om_core_script", script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {script}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    argv: list[str] = []
    if args.demo:
        argv.append("--demo")
    if args.train:
        argv.append("--train")
    if args.chat:
        argv.append("--chat")
    if args.device:
        argv.extend(["--device", args.device])
    if args.checkpoint:
        argv.extend(["--checkpoint", args.checkpoint])
    argv.extend(["--iters", str(args.iters)])
    raise SystemExit(mod.main(argv))


def om5_core_cmd(args):
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "om5_core.py"
    spec = importlib.util.spec_from_file_location("om5_core_script", script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {script}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    argv: list[str] = []
    if args.demo:
        argv.append("--demo")
    if args.train:
        argv.append("--train")
    if args.objective:
        argv.extend(["--objective", args.objective])
    if args.device:
        argv.extend(["--device", args.device])
    if args.checkpoint:
        argv.extend(["--checkpoint", args.checkpoint])
    if args.rag_scan is not None:
        argv.append("--rag-scan")
        argv.extend(list(args.rag_scan or []))
    argv.extend(["--iters", str(args.iters)])
    raise SystemExit(mod.main(argv))


def om_matrix_cmd(args):
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "om_matrix_production.py"
    spec = importlib.util.spec_from_file_location("om_matrix_script", script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {script}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    argv: list[str] = []
    if args.demo:
        argv.append("--demo")
    if args.train:
        argv.append("--train")
    if args.chat:
        argv.append("--chat")
    if args.ask:
        argv.extend(["--ask", args.ask])
    argv.extend(["--level", str(args.level)])
    if args.device:
        argv.extend(["--device", args.device])
    if args.checkpoint:
        argv.extend(["--checkpoint", args.checkpoint])
    argv.extend(["--iters", str(args.iters)])
    raise SystemExit(mod.main(argv))


def chatgpt_upgrade_cmd(args):
    """Audit Phase 1–3 ChatGPT-parity readiness and optionally write example datasets."""
    from om_ai.training.chatgpt_upgrade import (
        audit_chatgpt_parity,
        recommended_cli_commands,
        write_example_datasets,
    )

    tok = None
    if getattr(args, "tokenizer", None):
        from om_ai.tokenizer import load_tokenizer

        tok = load_tokenizer(args.tokenizer)
    audit = audit_chatgpt_parity(tokenizer=tok)
    payload = audit.as_dict()
    payload["next_commands"] = recommended_cli_commands()
    if getattr(args, "write_examples", False):
        payload["examples"] = write_example_datasets(Path("."))
    print(json.dumps(payload, indent=2))


def production_pipeline_cmd(args):
    """Status / dry-run / execute the Pretrain → SFT → DPO production pipeline."""
    from om_ai.training.production_pipeline import inventory_dict, pick_training_device, run_stage

    action = (getattr(args, "pipeline_action", None) or "status").strip().lower()
    if action in {"status", "inventory", "audit"}:
        print(json.dumps(inventory_dict(), indent=2))
        return
    stage = getattr(args, "stage", None) or action
    if stage in {"status", "inventory", "audit"}:
        print(json.dumps(inventory_dict(), indent=2))
        return
    device = getattr(args, "device", None) or pick_training_device()
    result = run_stage(
        stage,
        device=device,
        dry_run=not bool(getattr(args, "execute", False)),
        steps=getattr(args, "steps", None),
    )
    print(json.dumps(result, indent=2))


def sft(args):
    cfg, tok, model, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    ds = SFTDataset(args.data, tok, cfg.max_seq_len)
    tc = SFTConfig(
        steps=args.steps,
        batch_size=args.batch_size,
        grad_accum_steps=getattr(args, "grad_accum", 1),
        learning_rate=args.lr,
        precision=getattr(args, "precision", "auto"),
        output_dir=args.output,
        checkpoint_every=args.checkpoint_every,
    )
    print(
        json.dumps(
            {
                "stage": "sft",
                "device": str(dev),
                "rows": len(ds),
                "parameters": model.exact_parameter_count(),
                "grad_accum": tc.grad_accum_steps,
                "precision": tc.precision,
            }
        )
    )
    print(json.dumps(SFTTrainer(model, ds, tc, str(dev)).train(), indent=2))


def reward(args):
    cfg, tok, backbone, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    ds = PreferenceDataset(args.data, tok, cfg.max_seq_len)
    rm = RewardModel(backbone)
    rc = RewardConfig(steps=args.steps, batch_size=args.batch_size, learning_rate=args.lr, output_dir=args.output)
    print(json.dumps({"stage": "reward", "device": str(dev), "rows": len(ds)}))
    print(json.dumps(RewardTrainer(rm, ds, rc, str(dev)).train(), indent=2))


def dpo(args):
    cfg, tok, model, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    ds = PreferenceDataset(args.data, tok, cfg.max_seq_len)
    dc = DPOConfig(
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        beta=args.beta,
        output_dir=args.output,
    )
    print(json.dumps({"stage": "dpo", "device": str(dev), "rows": len(ds), "beta": args.beta}))
    print(json.dumps(DPOTrainer(model, ds, dc, str(dev)).train(), indent=2))


def ppo(args):
    """Smoke / infrastructure PPO: one policy update from synthetic rollouts.

    Real RLHF requires reward-model scoring + live rollouts. This command proves
    GAE + clipped surrogate + KL path executes on an OM checkpoint.
    """
    import copy

    cfg, tok, policy, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    ref = copy.deepcopy(policy)
    value_head = ValueHead(cfg.d_model).to(dev)
    pc = PPOConfig(lr=args.lr, ppo_epochs=max(1, args.epochs), kl_coef=args.kl_coef)
    trainer = PPOTrainer(policy, value_head, ref, pc, device=dev)

    prompt_ids = tok.encode(args.prompt, add_bos=True)[: max(1, cfg.max_seq_len // 4)]
    response_ids = tok.encode(args.response, add_eos=True)[: max(1, cfg.max_seq_len // 4)]
    if not response_ids:
        response_ids = [tok.eos_id]

    full = torch.tensor([prompt_ids + response_ids], dtype=torch.long, device=dev)
    resp_mask = torch.zeros_like(full, dtype=torch.bool)
    resp_mask[0, len(prompt_ids) :] = True
    with torch.no_grad():
        logprobs = trainer.compute_logprobs(policy, full, resp_mask).detach().cpu().tolist()
        ref_lp = trainer.compute_logprobs(ref, full, resp_mask).detach().cpu().tolist()
        out = policy(full, use_cache=False)
        hidden = out.get("last_hidden_state")
        if hidden is not None:
            vals = value_head(hidden[:, len(prompt_ids) :, :]).squeeze(0).detach().cpu().tolist()
            if isinstance(vals, float):
                vals = [vals]
        else:
            vals = [0.0] * len(response_ids)

    # Align lengths to response token count used by GAE
    t = len(response_ids)
    logprobs = (logprobs + [0.0] * t)[:t]
    ref_lp = (ref_lp + [0.0] * t)[:t]
    vals = (list(vals) + [0.0] * t)[:t]

    buf = RolloutBuffer(max_rollouts=max(1, args.rollouts))
    for _ in range(buf.max_rollouts):
        r = Rollout(
            prompt_ids=list(prompt_ids),
            response_ids=list(response_ids),
            logprobs=list(logprobs),
            ref_logprobs=list(ref_lp),
            values=list(vals),
            reward=float(args.reward),
        )
        compute_advantages(r, gamma=pc.gamma, lam=pc.lam)
        buf.add(r)

    stats = trainer.train_epoch(buf)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt = out_dir / "latest.pt"
    torch.save(
        {
            "model": policy.state_dict(),
            "value_head": value_head.state_dict(),
            "stage": "ppo",
            "trained": True,
            "stats": stats,
        },
        ckpt,
    )
    print(
        json.dumps(
            {
                "stage": "ppo",
                "device": str(dev),
                "rollouts": len(buf.rollouts),
                "checkpoint": str(ckpt),
                "note": "Synthetic rollouts prove infrastructure; not production RLHF",
                "stats": stats,
            },
            indent=2,
        )
    )


def generate(args):
    eng = LocalLLMEngine()
    print(eng.load(args.config, args.tokenizer, args.checkpoint, args.device))
    text = eng.generate(
        args.prompt,
        args.max_new_tokens,
        args.temperature,
        args.top_k,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
    )
    print(text)


def chat(args):
    eng = LocalLLMEngine()
    print(eng.load(args.config, args.tokenizer, args.checkpoint, args.device))
    messages = [{"role": "user", "content": args.message}]
    if args.system:
        messages = [{"role": "system", "content": args.system}] + messages
    print(eng.chat(messages, max_new_tokens=args.max_new_tokens, temperature=args.temperature))


def evaluate(args):
    _, tok, model, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    ev = EvaluationHarness(model, tok, dev)
    print(json.dumps({"smoke": ev.smoke_suite(), "perplexity": ev.perplexity(["OM AI is a private intelligence system."])}, indent=2))


def benchmark(args):
    _, tok, model, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    result = BenchmarkRunner(EvaluationHarness(model, tok, dev)).run(
        args.benchmark, args.report, args.max_new_tokens
    )
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))


def feedback_add(args):
    store = FeedbackStore(args.db)
    fid = store.add(args.prompt, args.response, args.rating, args.user_id, args.preferred_response, args.metadata)
    print(json.dumps({"id": fid}))


def feedback_export(args):
    store = FeedbackStore(args.db)
    sft_count = build_sft_replay(store, args.sft_output, args.min_rating)
    pref_count = build_preference_replay(store, args.preference_output)
    print(json.dumps({"sft_rows": sft_count, "preference_rows": pref_count}, indent=2))


def corpus_cmd(args):
    svc = CorpusService(output_dir=getattr(args, "workdir", "artifacts/corpus"))
    if args.sub == "import":
        print(json.dumps(svc.import_path(args.input, license=args.license, owner=args.owner, source_id=args.source_id), indent=2, default=str))
    elif args.sub == "validate":
        print(json.dumps(svc.validate_manifest(args.manifest), indent=2))
    elif args.sub == "dedupe":
        print(json.dumps(svc.dedupe(args.input, args.output), indent=2))
    elif args.sub == "audit":
        print(json.dumps(svc.audit(args.input, args.output), indent=2))
    elif args.sub == "shard":
        print(json.dumps(svc.shard(args.input, args.output, args.shard_size), indent=2))
    elif args.sub == "stats":
        print(json.dumps(svc.file_stats(args.input), indent=2))
    elif args.sub == "catalog":
        from om_ai.corpus import catalog_as_dicts

        print(json.dumps({"sources": catalog_as_dicts(training_only=args.training_only)}, indent=2))
    elif args.sub == "fetch":
        from om_ai.corpus import fetch_sources

        ids = [x.strip() for x in (args.sources or "").split(",") if x.strip()] or None
        results = fetch_sources(Path(args.root), ids, max_docs=args.max_docs)
        print(
            json.dumps(
                [
                    {
                        "source_id": r.source_id,
                        "path": r.path,
                        "docs": r.docs,
                        "bytes": r.bytes,
                        "ok": r.ok,
                        "detail": r.detail,
                    }
                    for r in results
                ],
                indent=2,
            )
        )
    elif args.sub == "build-v1":
        from om_ai.data_pipeline import run_omai_corpus_v1

        ids = [x.strip() for x in (args.sources or "").split(",") if x.strip()] or None
        report = run_omai_corpus_v1(
            args.root,
            fetch=not args.no_fetch,
            source_ids=ids,
            max_docs=args.max_docs,
        )
        print(json.dumps(report, indent=2, default=str))


def data_pipeline_cmd(args):
    from om_ai.data_pipeline import run_omai_corpus_v1
    from om_ai.data_pipeline.validator import validate_corpus
    from om_ai.tokenizer.omai_v1 import tokenizer_v1_status

    if args.sub == "run":
        ids = [x.strip() for x in (args.sources or "").split(",") if x.strip()] or None
        report = run_omai_corpus_v1(
            args.root,
            fetch=not args.no_fetch,
            source_ids=ids,
            max_docs=args.max_docs,
            tokenize=not args.no_tokenize,
        )
        print(json.dumps(report, indent=2, default=str))
    elif args.sub == "validate":
        print(json.dumps(validate_corpus(args.root), indent=2))
    elif args.sub == "tokenizer-status":
        print(json.dumps(tokenizer_v1_status(args.tokenizer), indent=2))


def genesis_cmd(args):
    if args.sub == "generate":
        from om_ai.genesis import write_dataset

        man = write_dataset(args.out, count=args.count)
        print(json.dumps(man, indent=2))
    elif args.sub == "domains":
        from om_ai.genesis.domains import layers_catalog

        print(json.dumps(layers_catalog(), indent=2))


def knowledge_brain_cmd(args):
    if args.sub == "catalog":
        from om_ai.knowledge_brain import knowledge_catalog

        print(json.dumps(knowledge_catalog(), indent=2))
    elif args.sub == "init":
        from om_ai.knowledge_brain import init_corpus

        print(json.dumps(init_corpus(args.root), indent=2))
    elif args.sub == "generate":
        from om_ai.knowledge_brain import write_instruct_dataset

        man = write_instruct_dataset(
            args.out,
            count=args.count,
            also_init_corpus=not args.no_init,
            root=args.root,
        )
        print(json.dumps(man, indent=2))
    elif args.sub == "directive":
        from om_ai.knowledge_brain.directive import KNOWLEDGE_DIRECTIVE, KNOWLEDGE_SYSTEM

        print(KNOWLEDGE_DIRECTIVE)
        print("\n--- system one-liner ---\n")
        print(KNOWLEDGE_SYSTEM)


def knowledge_universe_cmd(args):
    from om_ai.knowledge_universe import init_universe, process_stub, universe_status

    if args.sub == "init":
        print(json.dumps(init_universe(args.root), indent=2))
    elif args.sub == "status":
        print(json.dumps(universe_status(args.root), indent=2))
    elif args.sub == "process":
        print(json.dumps(process_stub(args.root), indent=2))


def brain_cmd(args):
    """Power OM chat from real local datasets (memory + QA retrieval)."""
    from om_ai.brain import power_from_datasets, status

    if args.sub == "status":
        print(json.dumps(status(), indent=2))
        return
    if args.sub == "power":
        report = power_from_datasets(
            limit_per_file=int(args.limit),
            stride=int(args.stride),
            also_rag=not args.no_rag,
            rag_limit=int(args.rag_limit),
        )
        print(json.dumps(report, indent=2))
        return
    if args.sub == "ask":
        from om_ai.brain.dataset_engine import retrieve_answer

        hit = retrieve_answer(args.query or "")
        print(json.dumps(hit or {"ok": False, "error": "no_match"}, indent=2, default=str))
        return
    raise SystemExit(f"unknown brain subcommand: {args.sub}")


def absolute_cmd(args):
    """OM Absolute Intelligence Architecture — cognitive OS cycle."""
    from om_ai.operating_intelligence import OperatingIntelligence, capability_status

    if args.sub == "status":
        print(json.dumps(capability_status(), indent=2))
        return
    if args.sub == "identity":
        from om_ai.identity import DIRECTIVE_MARKDOWN, identity_card

        print(DIRECTIVE_MARKDOWN)
        print("\n--- JSON ---\n")
        print(json.dumps(identity_card(), indent=2))
        return
    if args.sub == "cycle":
        result = OperatingIntelligence().run(
            args.goal,
            context={"actor": getattr(args, "actor", "") or ""},
            dry_run=True,
        )
        print("OM Absolute Intelligence Cycle")
        print(f"Intent: {(result.understood or {}).get('intent')}")
        print(f"Agents: {(result.agents or {}).get('agents')}")
        print(
            f"Knowledge: {(result.knowledge or {}).get('source')} "
            f"({(result.knowledge or {}).get('count')})"
        )
        print(f"Verified: {(result.verification or {}).get('ok')}")
        qg = (result.verification or {}).get("quality_gate") or {}
        print(f"Quality: {qg.get('ok')} issues={qg.get('issues')}")
        print("---")
        print(result.response)
        print("---")
        print(
            json.dumps(
                {
                    "meta": {
                        k: result.meta.get(k)
                        for k in ("architecture", "system_name", "assumption", "style")
                    },
                    "growth": result.growth,
                    "neural": (result.neural or {}).get("status"),
                },
                indent=2,
                default=str,
            )
        )
        return
    raise SystemExit(f"unknown absolute subcommand: {args.sub}")


def reason_cmd(args):
    from om_ai.reasoning import reason

    trace = reason(args.question)
    if args.json:
        print(json.dumps(trace.to_dict(), indent=2))
    else:
        print(trace.as_markdown())


def intent_cmd(args):
    from om_ai.core.intent_engine import classify, route

    c = classify(args.text)
    payload = {"classification": c.to_dict(), "route": route(c)}
    print(json.dumps(payload, indent=2))


def eval_suite_cmd(args):
    from om_ai.eval import run_suite

    complete_fn = None
    if args.config and args.tokenizer and args.checkpoint:
        _, tok, model, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
        harness = EvaluationHarness(model, tok, dev)

        def complete_fn(prompt: str, max_new: int) -> str:  # noqa: F811
            return harness.complete(prompt, max_new_tokens=max_new)

    result = run_suite(
        args.suite,
        complete_fn=complete_fn,
        max_new_tokens=args.max_new_tokens,
        report_path=args.out,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))


def coding_cmd(args):
    from om_ai.agent.coding_agent import plan_coding_task

    print(json.dumps(plan_coding_task(args.task, root=args.root, dry_run=not args.apply), indent=2))


def continuous_cmd(args):
    from om_ai.learning import run_learning_cycle

    if args.sub == "export":
        print(json.dumps(run_learning_cycle(out_dir=args.out), indent=2))


def upgrade_cmd(args):
    if args.target == "foundation":
        from om_ai.foundation import upgrade_foundation

        print(json.dumps(upgrade_foundation(args.root or None), indent=2))
    elif args.target == "sprint1":
        from om_ai.improvement import run_sprint1_demo
        from om_ai.knowledge.factory import process_document
        from om_ai.agents.runtime import run_agent
        from om_ai.core.response.intelligence import ensure_intelligent_response
        from pathlib import Path
        import time

        root = Path(args.root or Path.cwd()).resolve()
        sample = root / "data" / "om-foundation-corpus" / "raw" / "om_system_build_sample.txt"
        sample.parent.mkdir(parents=True, exist_ok=True)
        if not sample.is_file():
            sample.write_text(
                "OM Knowledge Factory sample. React FastAPI security validation testing.\n",
                encoding="utf-8",
            )
        report = {
            "name": "om-upgrade-sprint1",
            "ts": time.time(),
            "improvement_engine": run_sprint1_demo(),
            "knowledge_factory": process_document(sample),
            "agent_runtime": run_agent("Add health check endpoint", root=str(root), apply=False),
            "response_quality": ensure_intelligent_response(
                "Create React login page",
                "Rege — it’s Let’s a piece login maybe",
                intent="coding",
            ),
        }
        # drop huge nested markdown in CLI print
        rq = report["response_quality"]
        report["response_quality"] = {
            "repaired": rq.get("repaired"),
            "analysis": rq.get("analysis"),
            "final_preview": (rq.get("final") or "")[:500],
            "improvement_status": (rq.get("improvement") or {}).get("status"),
        }
        out = root / "artifacts" / "OM_UPGRADE_SPRINT1_REPORT.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        report["report_path"] = str(out)
        print(json.dumps(report, indent=2, default=str))
    else:
        raise SystemExit(f"Unknown upgrade target: {args.target}")


def improve_cmd(args):
    from om_ai.improvement import improve_from_exchange

    print(
        json.dumps(
            improve_from_exchange(args.question, args.answer, out_dir=args.out),
            indent=2,
            default=str,
        )
    )


def agent_runtime_cmd(args):
    from om_ai.agents.runtime import run_agent

    print(
        json.dumps(
            run_agent(args.task, root=args.root, apply=args.apply, run_tests=args.tests),
            indent=2,
            default=str,
        )
    )


def platform_cmd(args):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if args.sub == "build":
        from om_ai.platform import build_enterprise_platform

        print(json.dumps(build_enterprise_platform(args.root or None), indent=2, default=str))
    elif args.sub == "health":
        from services.api_gateway import APIGateway

        print(json.dumps(APIGateway().health(), indent=2, default=str))
    elif args.sub == "route":
        from services.api_gateway import APIGateway

        print(json.dumps(APIGateway().handle(args.path, **_platform_kwargs(args)), indent=2, default=str))
    elif args.sub == "workflow":
        from ai_platform.orchestration import OrchestrationPlatform

        print(
            json.dumps(
                OrchestrationPlatform().execute(args.request, root=args.root or "."),
                indent=2,
                default=str,
            )
        )
    else:
        raise SystemExit(f"Unknown platform subcommand: {args.sub}")


def _platform_kwargs(args) -> dict:
    kw = {}
    if getattr(args, "prompt", None):
        kw["prompt"] = args.prompt
        kw["question"] = args.prompt
    if getattr(args, "question", None):
        kw["question"] = args.question
        kw["prompt"] = args.question
    if getattr(args, "task", None):
        kw["task"] = args.task
    if getattr(args, "query", None):
        kw["query"] = args.query
    if getattr(args, "path_arg", None):
        kw["path"] = args.path_arg
    if getattr(args, "answer", None):
        kw["answer"] = args.answer
    return kw


def system_cmd(args):
    if args.sub == "build":
        from om_ai.system import system_build

        print(json.dumps(system_build(args.root or None), indent=2))
    elif args.sub == "check":
        from om_ai.system import self_check
        from pathlib import Path

        print(json.dumps(self_check(Path(args.root or Path.cwd()).resolve()), indent=2))


def knowledge_cmd(args):
    from om_ai.knowledge.engine import (
        knowledge_ingest,
        knowledge_status,
        ensure_knowledge_layout
    )

    if args.sub == "status":
        print(json.dumps(
            knowledge_status(args.root or None),
            indent=2
        ))

    elif args.sub == "init":
        print(json.dumps(
            ensure_knowledge_layout(args.root or None),
            indent=2
        ))

    elif args.sub == "ingest":
        print(json.dumps(
            knowledge_ingest(
                args.path,
                domain=args.domain or ""
            ),
            indent=2
        ))

    elif args.sub == "build":
        from om_ai.data_pipeline import run_omai_corpus_v1

        sources = [
            x.strip()
            for x in args.source.split(",")
            if x.strip()
        ]

        report = run_omai_corpus_v1(
            root=args.root,
            fetch=True,
            source_ids=sources,
            max_docs=args.max_docs
        )

        print(json.dumps(
            report,
            indent=2,
            default=str
        ))

def evaluate_run_cmd(args):
    from om_ai.evaluation import run_evaluation

    report = run_evaluation(out=args.out)
    scores = report.get("scores") or {}
    # Human-readable + JSON
    print("OM Evaluation Report")
    print(f"Reasoning Score: {scores.get('reasoning', scores.get('architecture', 0))}%")
    print(f"Coding Score: {scores.get('coding', 0)}%")
    print(f"Knowledge Score: {scores.get('knowledge', 0)}%")
    print(f"Math Score: {scores.get('math', 0)}%")
    print(f"Agents Score: {scores.get('agents', 0)}%")
    print(f"Security Score: {scores.get('security', 0)}%")
    print(f"Completeness: {scores.get('completeness', 0)}%")
    print(f"Improvement: {report.get('improvement', 'n/a')}")
    print(f"Report Generated: {args.out}")
    print(json.dumps(report, indent=2))


def registry_list(args):
    reg = ModelRegistry(args.root)
    print(json.dumps(reg.list_versions(), indent=2, default=str))


def registry_register(args):
    cfg, tok, model, _ = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    reg = ModelRegistry(args.root)
    meta = reg.register(
        args.model_id,
        model,
        args.tokenizer,
        training_data_version=args.data_version,
        initial_state="candidate",
        trained=args.trained,
        provenance={"architecture": args.architecture, "source_checkpoint": args.checkpoint},
    )
    print(json.dumps(meta, indent=2, default=str))


def bundle_save(args):
    cfg, tok, model, _ = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    root = save_bundle(
        args.output,
        model.state_dict(),
        cfg.to_dict(),
        args.tokenizer,
        training_state={"global_step": 0, "stage": args.stage},
        provenance={"trained": args.trained, "source_checkpoint": args.checkpoint},
        trained=args.trained,
    )
    print(json.dumps({"bundle": str(root), "integrity": verify_integrity(root)}, indent=2, default=str))


def project_scan(args):
    disc = ProjectDiscovery(args.root)
    result = disc.scan()
    payload = result.to_dict() if hasattr(result, "to_dict") else result
    print(json.dumps(payload, indent=2, default=str))


def train_om1(args):
    from om_ai.training.train_om1 import run_train_om1

    payload = run_train_om1(
        config=args.config,
        data=args.data,
        tokenizer=args.tokenizer,
        output=args.output,
        steps=args.steps,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
        max_tokens=args.max_tokens,
        max_docs=args.max_docs,
        checkpoint_every=args.checkpoint_every,
        log_every=args.log_every,
        precision=args.precision,
        resume=args.resume,
        allow_unbounded=args.allow_unbounded_steps,
    )
    print(json.dumps(payload, indent=2))


def train_70b(args):
    from om_ai.training.train_70b import run_train_70b

    st = run_train_70b(
        data=args.data,
        tokenizer=args.tokenizer,
        output=args.output,
        config=args.config,
        deepspeed_config=args.deepspeed,
        strategy=args.strategy,
        preflight_only=args.preflight_only,
        resume=args.resume,
        sft_data=args.sft_data,
        preference_data=args.preference_data,
        benchmark=args.benchmark,
        gates_path=args.gates,
        min_gpus=args.min_gpus,
        min_vram_gb=args.min_vram_gb,
        min_free_gb=args.min_free_gb,
        min_corpus_bytes=args.min_corpus_bytes,
        allow_cpu=args.allow_cpu,
        manifest=args.manifest,
        pretrain_steps=args.pretrain_steps,
        skip_posttrain=args.skip_posttrain,
    )
    print(json.dumps(st.to_dict(), indent=2))
    if st.stage == "FAILED":
        raise SystemExit(2)
    if args.preflight_only and st.artifacts.get("preflight_report"):
        report = json.loads(Path(st.artifacts["preflight_report"]).read_text())
        if not report.get("ok"):
            raise SystemExit(2)


def doctor(args):
    """Run full OM system diagnostics."""
    from om_ai.diagnostics import run_system_check

    report = run_system_check()
    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        print(report.format_report())
    if report.overall().startswith("DEGRADED") and any(
        i.status == "fail" for i in report.items if i.name.startswith(("Startup", "Brain"))
    ):
        raise SystemExit(1)


def status_cmd(args):
    """Print compact OM runtime status."""
    from om_ai.backends.checkpoint_checker import check_checkpoint, format_model_status
    from om_ai.diagnostics import run_system_check

    report = run_system_check()
    marks = report.summary_marks()
    ck = check_checkpoint(try_load=False)
    model_line = "Loaded" if ck.get("checkpoint") == "FOUND" and ck.get("loading") in {"READY", "SUCCESS", "PARTIAL"} else "Fallback (brain-only)"
    if ck.get("checkpoint") != "FOUND":
        model_line = "Missing → brain-only"

    agent_ok = sum(1 for i in report.items if i.name.startswith("Agents:") and i.status == "ok")
    print("OM AI STATUS")
    print("")
    print(f"Brain:     {'Running' if marks.get('Core Brain') == '✅' else 'Degraded'}")
    print(f"Agents:    {agent_ok} checks ok")
    print(f"Memory:    {'Connected' if marks.get('Memory') == '✅' else 'Check needed'}")
    print(f"Model:     {model_line}")
    print(f"Knowledge: {'Ready' if marks.get('Knowledge') in {'✅', '⚠️'} else 'Missing'}")
    print(f"Safety:    {'Ready' if marks.get('Safety') == '✅' else 'Check needed'}")
    print(f"Chat UI:   {'Ready' if marks.get('Chat UI') == '✅' else 'Missing'}")
    print("")
    print(f"System:    {report.overall()}")
    if getattr(args, "verbose", False):
        print("")
        print(format_model_status(ck))


def repair_cmd(args):
    """Create missing folders and initialize databases."""
    from om_ai.diagnostics.repair import repair_system

    result = repair_system()
    print(json.dumps(result, indent=2))
    print("")
    print("Repair complete. Run: om-ai doctor")


def serve(args):
    import os
    import sys
    import uvicorn

    from om_ai.env import load_dotenv

    # ``.env`` is a file — it is not automatically the process environment.
    # Load once here so `om-ai serve` picks up OM_AI_* without `source .env`.
    loaded = load_dotenv()
    if loaded is not None:
        print(f"Loaded environment from {loaded}", file=sys.stderr)

    # Never silently start a 70B training job from the API server.
    if os.getenv("OM_AI_AUTO_TRAIN_70B", "0") == "1":
        print(
            "WARNING: OM_AI_AUTO_TRAIN_70B=1 is set but ignored by `om-ai serve`. "
            "Training must be started deliberately with:\n"
            "  om-ai train-70b --data ... --tokenizer ... --output ...",
            file=sys.stderr,
        )

    # Prefer OM native checkpoint paths; READY banner prints from api.main on load.
    os.environ.setdefault("OM_MODEL_PROVIDER", "om_native")
    os.environ.setdefault("OM_AI_CHAT_BACKEND", "om_native")

    try:
        from om_ai.diagnostics.logging_setup import setup_logging
        from om_ai.diagnostics.repair import repair_system

        setup_logging()
        if os.getenv("OM_AI_AUTO_REPAIR", "1") == "1":
            repair_system(load_env=False)
    except Exception as exc:
        print(f"Startup repair/logging skipped: {exc}", file=sys.stderr)

    uvicorn.run("om_ai.api.main:app", host=args.host, port=args.port, reload=args.reload)


def main():
    p = argparse.ArgumentParser(prog="om-ai", description="OM AI Operating Brain CLI")
    sp = p.add_subparsers(dest="cmd", required=True)

    mi = sp.add_parser("model-info")
    mi.add_argument(
        "--config",
        required=False,
        help="Architecture JSON. Omit for OM-1.0 native registry summary.",
    )
    mi.add_argument("--tokenizer")
    mi.add_argument(
        "--native",
        action="store_true",
        help="Show OM-1.0 native backend / registry info (default when --config omitted).",
    )
    mi.set_defaults(func=model_info)

    t = sp.add_parser("tokenizer")
    tsp = t.add_subparsers(dest="sub", required=True)
    tt = tsp.add_parser("train")
    tt.add_argument("--input", required=True)
    tt.add_argument("--output", required=True)
    tt.add_argument("--vocab-size", type=int, default=1024)
    tt.add_argument("--min-pair-freq", type=int, default=2)
    tt.set_defaults(func=tokenizer_train)
    ti = tsp.add_parser("inspect")
    ti.add_argument("--tokenizer", required=True)
    ti.set_defaults(func=tokenizer_inspect)
    te = tsp.add_parser("encode")
    te.add_argument("--tokenizer", required=True)
    te.add_argument("--text", required=True)
    te.add_argument("--bos", action="store_true")
    te.add_argument("--eos", action="store_true")
    te.set_defaults(func=tokenizer_encode)
    td = tsp.add_parser("decode")
    td.add_argument("--tokenizer", required=True)
    td.add_argument("--ids", required=True)
    td.set_defaults(func=tokenizer_decode)

    # aliases for master prompt naming
    pre = sp.add_parser("pretrain")
    for name in ("pretrain", "train"):
        tr = pre if name == "pretrain" else sp.add_parser("train")
        tr.add_argument("--config", required=True)
        tr.add_argument("--data", required=True)
        tr.add_argument("--tokenizer", required=True)
        tr.add_argument("--steps", type=int, default=1000)
        tr.add_argument("--batch-size", type=int, default=4)
        tr.add_argument("--grad-accum", type=int, default=1)
        tr.add_argument("--precision", default="auto", choices=["auto", "fp32", "fp16", "bf16"])
        tr.add_argument("--lr", type=float, default=3e-4)
        tr.add_argument("--output", default="artifacts/checkpoints")
        tr.add_argument("--checkpoint-every", type=int, default=100)
        tr.add_argument("--log-every", type=int, default=10)
        tr.add_argument("--resume")
        tr.add_argument("--device")
        tr.add_argument("--gradient-checkpointing", action="store_true")
        tr.set_defaults(func=train)

    tom = sp.add_parser(
        "train-om",
        help="Scratch-to-training script (train_om.py) on Mac MPS — bpe/toy/production",
    )
    tom.add_argument("--mode", choices=("bpe", "toy", "production"), default="bpe")
    tom.add_argument("--device", default="")
    tom.add_argument("--data", default="")
    tom.add_argument("--config", default="")
    tom.add_argument("--tokenizer", default="")
    tom.add_argument(
        "--output",
        default="artifacts/checkpoints/om-1.0-scratch/om1_weights.pt",
    )
    tom.add_argument("--batch-size", type=int, default=32)
    tom.add_argument("--block-size", type=int, default=128)
    tom.add_argument("--max-iters", type=int, default=500)
    tom.add_argument("--lr", type=float, default=3e-4)
    tom.add_argument("--eval-interval", type=int, default=100)
    tom.add_argument("--vocab-size", type=int, default=2000)
    tom.add_argument(
        "--build-knowledge",
        nargs="*",
        metavar="DIR",
        default=None,
        help="Aggregate offline local docs into knowledge.txt",
    )
    tom.add_argument("--knowledge-out", default="knowledge.txt")
    tom.add_argument("--train-after-build", action="store_true")
    tom.set_defaults(func=train_om_cmd)

    oc = sp.add_parser(
        "om-core",
        help="Level-1 OM core engine (Pre-LN/SwiGLU, tools, checkpoints) → om_core.py",
    )
    oc.add_argument("--demo", action="store_true")
    oc.add_argument("--train", action="store_true")
    oc.add_argument("--chat", action="store_true")
    oc.add_argument("--device", default="")
    oc.add_argument("--checkpoint", default="artifacts/om_core/weights.pt")
    oc.add_argument("--iters", type=int, default=400)
    oc.set_defaults(func=om_core_cmd)

    o5 = sp.add_parser(
        "om5",
        help="OM-5.0 matrix scaffold (thought/CoT, sandbox, RAG scan, multi-agent plan)",
    )
    o5.add_argument("--demo", action="store_true")
    o5.add_argument("--train", action="store_true")
    o5.add_argument("--objective", default="")
    o5.add_argument("--device", default="")
    o5.add_argument("--checkpoint", default="artifacts/om5_core/weights.pt")
    o5.add_argument("--iters", type=int, default=300)
    o5.add_argument("--rag-scan", nargs="*", default=None)
    o5.set_defaults(func=om5_core_cmd)

    omx = sp.add_parser(
        "matrix",
        help="OM Master Matrix L1–L5 scaffold (om_matrix_production.py) + chat/checkpoints",
    )
    omx.add_argument("--demo", action="store_true")
    omx.add_argument("--train", action="store_true")
    omx.add_argument("--chat", action="store_true")
    omx.add_argument("--ask", default="")
    omx.add_argument("--level", type=float, default=1.0)
    omx.add_argument("--device", default="")
    omx.add_argument("--checkpoint", default="artifacts/om_matrix/weights.pt")
    omx.add_argument("--iters", type=int, default=300)
    omx.set_defaults(func=om_matrix_cmd)

    up = sp.add_parser(
        "chatgpt-upgrade",
        help="Audit OM-1.0 ChatGPT-parity (sampling, RoPE/RMSNorm/SwiGLU/SDPA, SFT/DPO)",
    )
    up.add_argument("--tokenizer", default="")
    up.add_argument(
        "--write-examples",
        action="store_true",
        help="Write data/sft and data/dpo example JSONL templates",
    )
    up.set_defaults(func=chatgpt_upgrade_cmd)

    pp = sp.add_parser(
        "production-pipeline",
        help="3-stage ChatGPT pipeline inventory + Pretrain/SFT/DPO launchers (MPS on Mac)",
    )
    pp.add_argument(
        "pipeline_action",
        nargs="?",
        default="status",
        help="status | pretrain | sft | dpo",
    )
    pp.add_argument("--stage", default="", help="Alias for pipeline_action")
    pp.add_argument("--device", default="", help="Force device (default: MPS on Mac)")
    pp.add_argument(
        "--execute",
        action="store_true",
        help="Actually run training (default is dry-run command print)",
    )
    pp.add_argument("--steps", type=int, default=None)
    pp.set_defaults(func=production_pipeline_cmd)

    sf = sp.add_parser("sft")
    sfs = sf.add_subparsers(dest="sft_sub")
    sft_train = sfs.add_parser("train") if False else sf  # flat + nested
    # Support both `om-ai sft ...` and `om-ai sft train ...`
    sf.add_argument("--config", required=True)
    sf.add_argument("--data", required=True)
    sf.add_argument("--tokenizer", required=True)
    sf.add_argument("--checkpoint", required=True)
    sf.add_argument("--steps", type=int, default=1000)
    sf.add_argument("--batch-size", type=int, default=2)
    sf.add_argument("--grad-accum", type=int, default=1)
    sf.add_argument("--precision", default="auto", choices=["auto", "fp32", "fp16", "bf16"])
    sf.add_argument("--lr", type=float, default=2e-5)
    sf.add_argument("--output", default="artifacts/sft")
    sf.add_argument("--checkpoint-every", type=int, default=100)
    sf.add_argument("--device")
    sf.set_defaults(func=sft)

    rw = sp.add_parser("reward")
    rw.add_argument("--config", required=True)
    rw.add_argument("--data", required=True)
    rw.add_argument("--tokenizer", required=True)
    rw.add_argument("--checkpoint", required=True)
    rw.add_argument("--steps", type=int, default=500)
    rw.add_argument("--batch-size", type=int, default=2)
    rw.add_argument("--lr", type=float, default=1e-5)
    rw.add_argument("--output", default="artifacts/reward")
    rw.add_argument("--device")
    rw.set_defaults(func=reward)

    dp = sp.add_parser("dpo")
    dp.add_argument("--config", required=True)
    dp.add_argument("--data", required=True)
    dp.add_argument("--tokenizer", required=True)
    dp.add_argument("--checkpoint", required=True)
    dp.add_argument("--steps", type=int, default=500)
    dp.add_argument("--batch-size", type=int, default=2)
    dp.add_argument("--lr", type=float, default=1e-6)
    dp.add_argument("--beta", type=float, default=0.1)
    dp.add_argument("--output", default="artifacts/dpo")
    dp.add_argument("--device")
    dp.set_defaults(func=dpo)

    pp = sp.add_parser("ppo", help="PPO/RLHF infrastructure smoke (synthetic rollouts)")
    pp.add_argument("--config", required=True)
    pp.add_argument("--tokenizer", required=True)
    pp.add_argument("--checkpoint", required=True)
    pp.add_argument("--output", default="artifacts/ppo")
    pp.add_argument("--lr", type=float, default=1e-5)
    pp.add_argument("--epochs", type=int, default=1)
    pp.add_argument("--rollouts", type=int, default=2)
    pp.add_argument("--reward", type=float, default=1.0)
    pp.add_argument("--kl-coef", type=float, default=0.1)
    pp.add_argument("--prompt", default="User: hello")
    pp.add_argument("--response", default="Assistant: hi")
    pp.add_argument("--device")
    pp.set_defaults(func=ppo)

    g = sp.add_parser("generate")
    g.add_argument("--config", required=True)
    g.add_argument("--tokenizer", required=True)
    g.add_argument("--checkpoint", required=True)
    g.add_argument("--prompt", required=True)
    g.add_argument("--max-new-tokens", type=int, default=64)
    g.add_argument("--temperature", type=float, default=0.8)
    g.add_argument("--top-k", type=int, default=50)
    g.add_argument("--top-p", type=float, default=1.0)
    g.add_argument("--repetition-penalty", type=float, default=1.0)
    g.add_argument("--device")
    g.set_defaults(func=generate)

    ch = sp.add_parser("chat")
    ch.add_argument("--config", required=True)
    ch.add_argument("--tokenizer", required=True)
    ch.add_argument("--checkpoint", required=True)
    ch.add_argument("--message", required=True)
    ch.add_argument("--system", default="")
    ch.add_argument("--max-new-tokens", type=int, default=64)
    ch.add_argument("--temperature", type=float, default=0.8)
    ch.add_argument("--device")
    ch.set_defaults(func=chat)

    b = sp.add_parser("benchmark")
    b.add_argument("--config", required=True)
    b.add_argument("--tokenizer", required=True)
    b.add_argument("--checkpoint", required=True)
    b.add_argument("--benchmark", default="benchmarks/core.jsonl")
    b.add_argument("--report", default="artifacts/eval/report.json")
    b.add_argument("--max-new-tokens", type=int, default=32)
    b.add_argument("--device")
    b.set_defaults(func=benchmark)

    fb = sp.add_parser("feedback")
    fsp = fb.add_subparsers(dest="sub", required=True)
    fa = fsp.add_parser("add")
    fa.add_argument("--db", default="artifacts/feedback.sqlite3")
    fa.add_argument("--prompt", required=True)
    fa.add_argument("--response", required=True)
    fa.add_argument("--rating", type=int, required=True)
    fa.add_argument("--user-id", default="")
    fa.add_argument("--preferred-response", default="")
    fa.add_argument("--metadata", default="")
    fa.set_defaults(func=feedback_add)
    fx = fsp.add_parser("export")
    fx.add_argument("--db", default="artifacts/feedback.sqlite3")
    fx.add_argument("--sft-output", default="artifacts/feedback_sft.jsonl")
    fx.add_argument("--preference-output", default="artifacts/feedback_preferences.jsonl")
    fx.add_argument("--min-rating", type=int, default=4)
    fx.set_defaults(func=feedback_export)

    c = sp.add_parser("corpus")
    csp = c.add_subparsers(dest="sub", required=True)
    for sub, needs in [
        ("import", True),
        ("validate", False),
        ("dedupe", True),
        ("audit", True),
        ("shard", True),
        ("stats", True),
    ]:
        cp = csp.add_parser(sub)
        cp.add_argument("--workdir", default="artifacts/corpus")
        if sub == "validate":
            cp.add_argument("--manifest", required=True)
        elif sub == "import":
            cp.add_argument("--input", required=True)
            cp.add_argument("--license", default="proprietary-owned")
            cp.add_argument("--owner", default="om-ai")
            cp.add_argument("--source-id", default="import-1")
        else:
            cp.add_argument("--input", required=True)
            if sub in {"dedupe", "audit", "shard"}:
                cp.add_argument("--output", required=True)
            if sub == "shard":
                cp.add_argument("--shard-size", type=int, default=1000)
        cp.set_defaults(func=corpus_cmd)

    cc = csp.add_parser("catalog", help="List approved open training-data sources")
    cc.add_argument("--training-only", action="store_true")
    cc.set_defaults(func=corpus_cmd, workdir="artifacts/corpus")

    cf = csp.add_parser("fetch", help="Fetch licensed sample sources into OMAI-Corpus-v1/raw")
    cf.add_argument("--root", default="data/omai-corpus-v1")
    cf.add_argument("--sources", default="", help="Comma list: wikipedia-en,gutenberg,fineweb,open-assistant,om-owned")
    cf.add_argument("--max-docs", type=int, default=40)
    cf.set_defaults(func=corpus_cmd, workdir="artifacts/corpus")

    cb = csp.add_parser("build-v1", help="Build OMAI-Corpus-v1 (fetch→clean→dedupe→train/val)")
    cb.add_argument("--root", default="data/omai-corpus-v1")
    cb.add_argument("--sources", default="")
    cb.add_argument("--max-docs", type=int, default=40)
    cb.add_argument("--no-fetch", action="store_true", help="Only rebuild from existing raw/")
    cb.set_defaults(func=corpus_cmd, workdir="artifacts/corpus")

    dp = sp.add_parser("data-pipeline", help="OMAI-Corpus-v1 factory (Own Model Roadmap Phase 1–2)")
    dps = dp.add_subparsers(dest="sub", required=True)
    dpr = dps.add_parser("run", help="Raw→clean→filter→dedupe→tokenize→train/val")
    dpr.add_argument("--root", default="data/omai-corpus-v1")
    dpr.add_argument("--sources", default="")
    dpr.add_argument("--max-docs", type=int, default=40)
    dpr.add_argument("--no-fetch", action="store_true")
    dpr.add_argument("--no-tokenize", action="store_true")
    dpr.set_defaults(func=data_pipeline_cmd)
    dpv = dps.add_parser("validate", help="Validate corpus folder layout")
    dpv.add_argument("--root", default="data/omai-corpus-v1")
    dpv.set_defaults(func=data_pipeline_cmd)
    dpt = dps.add_parser("tokenizer-status", help="OMAI-Tokenizer-v1 special-token status")
    dpt.add_argument("--tokenizer", default="artifacts/tokenizer-production-65536.json")
    dpt.set_defaults(func=data_pipeline_cmd)

    ge = sp.add_parser("genesis", help="OM-1.0 Genesis-JARVIS intelligence dataset")
    ges = ge.add_subparsers(dest="sub", required=True)
    geg = ges.add_parser("generate", help="Generate instruction SFT JSONL")
    geg.add_argument(
        "--out",
        default="data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl",
    )
    geg.add_argument("--count", type=int, default=1000)
    geg.set_defaults(func=genesis_cmd)
    ged = ges.add_parser("domains", help="List Genesis training domains")
    ged.set_defaults(func=genesis_cmd)

    kb = sp.add_parser(
        "knowledge-brain",
        help="OM Universal Knowledge Brain (1600–2026 eras + domains)",
    )
    kbs = kb.add_subparsers(dest="sub", required=True)
    kbc = kbs.add_parser("catalog", help="Print eras + domains catalog JSON")
    kbc.set_defaults(func=knowledge_brain_cmd)
    kbi = kbs.add_parser("init", help="Create knowledge folder tree under data/")
    kbi.add_argument("--root", default="data/om-knowledge-brain-v1")
    kbi.set_defaults(func=knowledge_brain_cmd)
    kbg = kbs.add_parser("generate", help="Generate knowledge instruct SFT JSONL")
    kbg.add_argument("--root", default="data/om-knowledge-brain-v1")
    kbg.add_argument(
        "--out",
        default="data/om-knowledge-brain-v1/train/om_knowledge_instruct_v1.jsonl",
    )
    kbg.add_argument("--count", type=int, default=2000)
    kbg.add_argument("--no-init", action="store_true", help="Skip corpus folder init")
    kbg.set_defaults(func=knowledge_brain_cmd)
    kbd = kbs.add_parser("directive", help="Print master knowledge directive")
    kbd.set_defaults(func=knowledge_brain_cmd)

    ku = sp.add_parser(
        "knowledge-universe",
        help="Massive Knowledge Universe corpus layout (books/papers/code/…)",
    )
    kus = ku.add_subparsers(dest="sub", required=True)
    kui = kus.add_parser("init", help="Create knowledge/ bucket tree")
    kui.add_argument("--root", default="data/om-knowledge-universe-v1")
    kui.set_defaults(func=knowledge_universe_cmd)
    kus2 = kus.add_parser("status", help="Count raw files per bucket")
    kus2.add_argument("--root", default="data/om-knowledge-universe-v1")
    kus2.set_defaults(func=knowledge_universe_cmd)
    kup = kus.add_parser("process", help="Write clean/dedupe/embed process plan")
    kup.add_argument("--root", default="data/om-knowledge-universe-v1")
    kup.set_defaults(func=knowledge_universe_cmd)

    br = sp.add_parser(
        "brain",
        help="Power chat from real datasets (QA memory + RAG) — not static templates",
    )
    brs = br.add_subparsers(dest="sub", required=True)
    brp = brs.add_parser("power", help="Ingest knowledge-brain / genesis / chat SFT into QA+RAG")
    brp.add_argument("--limit", type=int, default=8000, help="Max pairs per corpus file")
    brp.add_argument("--stride", type=int, default=5, help="Take every Nth line (1=all)")
    brp.add_argument("--rag-limit", type=int, default=2500, help="Pairs also written into RAG KB")
    brp.add_argument("--no-rag", action="store_true", help="Skip RAG KB ingest")
    brp.set_defaults(func=brain_cmd)
    brst = brs.add_parser("status", help="Show dataset-brain pair counts")
    brst.set_defaults(func=brain_cmd)
    bra = brs.add_parser("ask", help="Retrieve a dataset-grounded answer (debug)")
    bra.add_argument("query")
    bra.set_defaults(func=brain_cmd)

    ab = sp.add_parser(
        "absolute",
        help="OM Absolute Intelligence Architecture (cognitive OS status/cycle)",
    )
    abs_ = ab.add_subparsers(dest="sub", required=True)
    abs_st = abs_.add_parser("status", help="Layer capability board")
    abs_st.set_defaults(func=absolute_cmd)
    abs_id = abs_.add_parser("identity", help="Print OM Operating Mind Genesis identity")
    abs_id.set_defaults(func=absolute_cmd)
    abs_cy = abs_.add_parser("cycle", help="Run Observe→Learn cognitive cycle")
    abs_cy.add_argument("goal")
    abs_cy.add_argument("--actor", default="")
    abs_cy.set_defaults(func=absolute_cmd)

    rs = sp.add_parser("reason", help="OM reasoning engine (decompose→plan→verify→critique)")
    rs.add_argument("question")
    rs.add_argument("--json", action="store_true")
    rs.set_defaults(func=reason_cmd)

    intentp = sp.add_parser("intent", help="OM intent engine (classify → route)")
    intents = intentp.add_subparsers(dest="sub", required=True)
    intentc = intents.add_parser("classify", help="Classify user text intent/domain/agent")
    intentc.add_argument("text")
    intentc.set_defaults(func=intent_cmd)

    evs = sp.add_parser("eval", help="OM Evaluation Platform")
    evss = evs.add_subparsers(dest="sub", required=True)
    evsuite = evss.add_parser("suite", help="Run om_eval_suite_v1 (heuristic or model)")
    evsuite.add_argument("--suite", default="benchmarks/om_eval_suite_v1.jsonl")
    evsuite.add_argument("--out", default="artifacts/eval/latest.json")
    evsuite.add_argument("--config", default="")
    evsuite.add_argument("--tokenizer", default="")
    evsuite.add_argument("--checkpoint", default="")
    evsuite.add_argument("--max-new-tokens", type=int, default=64)
    evsuite.add_argument("--device")
    evsuite.set_defaults(func=eval_suite_cmd)

    cd = sp.add_parser("coding", help="OM Coding Agent")
    cds = cd.add_subparsers(dest="sub", required=True)
    cdp = cds.add_parser("plan", help="Plan a coding task against a repo (dry-run)")
    cdp.add_argument("--task", required=True)
    cdp.add_argument("--root", default=".")
    cdp.add_argument("--apply", action="store_true", help="Request apply mode (still gated)")
    cdp.set_defaults(func=coding_cmd)

    cont = sp.add_parser("continuous", help="Continuous learning cycle")
    conts = cont.add_subparsers(dest="sub", required=True)
    conte = conts.add_parser("export", help="Export feedback → SFT/DPO recipe bundle")
    conte.add_argument("--out", default="data/continuous")
    conte.add_argument("--db", default="artifacts/feedback.sqlite3")
    conte.set_defaults(func=continuous_cmd)

    up = sp.add_parser("upgrade", help="Run OM foundation / platform upgrades")
    up.add_argument("target", choices=["foundation", "sprint1"], help="Upgrade target")
    up.add_argument("--root", default="", help="Repo root (default: cwd)")
    up.set_defaults(func=upgrade_cmd)

    imp = sp.add_parser("improve", help="OM Self-Improvement Engine (score → dataset → queue)")
    imp.add_argument("--question", required=True)
    imp.add_argument("--answer", required=True)
    imp.add_argument("--out", default="data/om_training/improvements")
    imp.set_defaults(func=improve_cmd)

    ar = sp.add_parser("agent-runtime", help="OM Agent Runtime (route → plan → gated act)")
    ar.add_argument("--task", required=True)
    ar.add_argument("--root", default=".")
    ar.add_argument("--apply", action="store_true")
    ar.add_argument("--tests", action="store_true")
    ar.set_defaults(func=agent_runtime_cmd)

    plat = sp.add_parser("platform", help="OM Enterprise Production Platform")
    plats = plat.add_subparsers(dest="sub", required=True)
    platb = plats.add_parser("build", help="Build/verify enterprise architecture")
    platb.add_argument("--root", default="")
    platb.set_defaults(func=platform_cmd)
    plath = plats.add_parser("health", help="API gateway + services health")
    plath.set_defaults(func=platform_cmd)
    platr = plats.add_parser("route", help="Route through API/Model gateway")
    platr.add_argument("--path", required=True, help="chat|reason|agent|knowledge.search|evaluate|improve|metrics")
    platr.add_argument("--prompt", default="")
    platr.add_argument("--question", default="")
    platr.add_argument("--task", default="")
    platr.add_argument("--query", default="")
    platr.add_argument("--path-arg", default="", dest="path_arg")
    platr.add_argument("--answer", default="")
    platr.set_defaults(func=platform_cmd)
    platw = plats.add_parser("workflow", help="Run orchestration workflow")
    platw.add_argument("--request", required=True)
    platw.add_argument("--root", default=".")
    platw.set_defaults(func=platform_cmd)

    sysp = sp.add_parser("system", help="OM production system build / self-check")
    syss = sysp.add_subparsers(dest="sub", required=True)
    sysb = syss.add_parser("build", help="Build production foundation + verify")
    sysb.add_argument("--root", default="")
    sysb.set_defaults(func=system_cmd)
    sysc = syss.add_parser("check", help="Run self-check only")
    sysc.add_argument("--root", default="")
    sysc.set_defaults(func=system_cmd)

    kn = sp.add_parser("knowledge", help="Knowledge Corpus Engine")
    kns = kn.add_subparsers(dest="sub", required=True)
    knb = kns.add_parser("build", help="Build knowledge corpus from sources")
    knb.add_argument(
        "--source",
        default="",
        help="Source name: fineweb,wikipedia,gutenberg,etc"
    )
    knb.add_argument(
        "--root",
        default="data/omai-corpus-v1"
    )
    knb.add_argument(
        "--max-docs",
        type=int,
        default=100
    )
    knb.set_defaults(func=knowledge_cmd)
    knst = kns.add_parser("status", help="Knowledge Engine READY status")
    knst.add_argument("--root", default="")
    knst.set_defaults(func=knowledge_cmd)
    kni = kns.add_parser("init", help="Ensure corpus directories")
    kni.add_argument("--root", default="")
    kni.set_defaults(func=knowledge_cmd)
    knin = kns.add_parser("ingest", help="Ingest a document into RAG")
    knin.add_argument("path")
    knin.add_argument("--domain", default="")
    knin.set_defaults(func=knowledge_cmd)

    # Alias: om-ai evaluate run  (legacy model smoke: om-ai evaluate model)
    evrun = sp.add_parser("evaluate")
    evrs = evrun.add_subparsers(dest="sub", required=True)
    evrr = evrs.add_parser("run", help="Run evaluation suite + scores report")
    evrr.add_argument("--out", default="artifacts/eval/foundation_report.json")
    evrr.set_defaults(func=evaluate_run_cmd)
    evrl = evrs.add_parser("model", help="Legacy model smoke/perplexity eval")
    evrl.add_argument("--config", required=True)
    evrl.add_argument("--tokenizer", required=True)
    evrl.add_argument("--checkpoint", required=True)
    evrl.add_argument("--device")
    evrl.set_defaults(func=evaluate)

    rg = sp.add_parser("registry")
    rgs = rg.add_subparsers(dest="sub", required=True)
    rl = rgs.add_parser("list")
    rl.add_argument("--root", default="artifacts/registry")
    rl.set_defaults(func=registry_list)
    rr = rgs.add_parser("register")
    rr.add_argument("--root", default="artifacts/registry")
    rr.add_argument("--model-id", required=True)
    rr.add_argument("--config", required=True)
    rr.add_argument("--tokenizer", required=True)
    rr.add_argument("--checkpoint", required=True)
    rr.add_argument("--architecture", default="om-transformer")
    rr.add_argument("--data-version", default="dev")
    rr.add_argument("--trained", action="store_true")
    rr.add_argument("--device")
    rr.set_defaults(func=registry_register)

    bn = sp.add_parser("bundle")
    bn.add_argument("--config", required=True)
    bn.add_argument("--tokenizer", required=True)
    bn.add_argument("--checkpoint", required=True)
    bn.add_argument("--output", required=True)
    bn.add_argument("--stage", default="candidate")
    bn.add_argument("--trained", action="store_true")
    bn.add_argument("--device")
    bn.set_defaults(func=bundle_save)

    pr = sp.add_parser("project-scan")
    pr.add_argument("--root", required=True)
    pr.set_defaults(func=project_scan)

    t1 = sp.add_parser(
        "train-om1",
        help="OM-1.0 local/smoke train (streaming corpus; not 70B).",
    )
    t1.add_argument("--config", default="configs/om-1.0-local.json")
    t1.add_argument("--data", help="JSONL or text corpus (streamed line-by-line)")
    t1.add_argument("--tokenizer", help="OM ByteBPE or HF chat tokenizer JSON")
    t1.add_argument("--output", default="artifacts/checkpoints/om-1.0-smoke")
    t1.add_argument("--steps", type=int, default=20)
    t1.add_argument("--batch-size", type=int, default=4)
    t1.add_argument("--lr", type=float, default=3e-4)
    t1.add_argument("--device")
    t1.add_argument("--max-tokens", type=int, default=250_000)
    t1.add_argument("--max-docs", type=int, default=2000)
    t1.add_argument("--checkpoint-every", type=int, default=10)
    t1.add_argument("--log-every", type=int, default=1)
    t1.add_argument("--precision", default="auto", choices=["auto", "fp32", "fp16", "bf16"])
    t1.add_argument("--resume")
    t1.add_argument(
        "--allow-unbounded-steps",
        action="store_true",
        help="Allow >250k steps on MPS/CPU. Still cannot match ChatGPT on this architecture.",
    )
    t1.set_defaults(func=train_om1)

    t70 = sp.add_parser(
        "train-70b",
        help="OM-70B training launcher (preflight + ZeRO-3/FSDP). Does not run from serve.",
    )
    t70.add_argument("--data", required=True, help="Licensed corpus path (file or directory)")
    t70.add_argument("--tokenizer", required=True)
    t70.add_argument("--output", required=True, help="Checkpoint / status output directory")
    t70.add_argument("--config", default="configs/70b.json")
    t70.add_argument("--deepspeed", default="configs/deepspeed_zero3.json")
    t70.add_argument("--strategy", choices=["deepspeed_zero3", "fsdp"], default="deepspeed_zero3")
    t70.add_argument("--preflight-only", action="store_true")
    t70.add_argument("--resume", action="store_true")
    t70.add_argument("--sft-data")
    t70.add_argument("--preference-data")
    t70.add_argument("--benchmark")
    t70.add_argument("--gates", default="configs/train_70b_gates.json")
    t70.add_argument("--manifest", help="Optional corpus license manifest JSON")
    t70.add_argument("--min-gpus", type=int, default=8)
    t70.add_argument("--min-vram-gb", type=float, default=40.0)
    t70.add_argument("--min-free-gb", type=float, default=500.0)
    t70.add_argument("--min-corpus-bytes", type=int, default=1_000_000)
    t70.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Dev only: do not require CUDA (will still not produce a real 70B brain)",
    )
    t70.add_argument("--pretrain-steps", type=int, default=1000)
    t70.add_argument("--skip-posttrain", action="store_true")
    t70.set_defaults(func=train_70b)

    s = sp.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8080)
    s.add_argument("--reload", action="store_true")
    s.set_defaults(func=serve)

    doc = sp.add_parser("doctor", help="Full OM system diagnostics health report")
    doc.add_argument("--json", action="store_true", help="Print JSON report")
    doc.set_defaults(func=doctor)

    stc = sp.add_parser("status", help="Compact OM brain / agents / memory / model status")
    stc.add_argument("--verbose", "-v", action="store_true")
    stc.set_defaults(func=status_cmd)

    rep = sp.add_parser("repair", help="Create missing folders and initialize databases")
    rep.set_defaults(func=repair_cmd)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
