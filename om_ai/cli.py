from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer, load_tokenizer
from om_ai.data import DatasetPipeline
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
)
from om_ai.eval import EvaluationHarness, BenchmarkRunner
from om_ai.runtime import LocalLLMEngine
from om_ai.continuous import FeedbackStore, build_sft_replay, build_preference_replay
from om_ai.corpus import CorpusService
from om_ai.registry import ModelRegistry
from om_ai.checkpoint import save_bundle, verify_integrity
from om_ai.discovery import ProjectDiscovery


def load_model(config_path, tokenizer_path, checkpoint=None, device=None):
    cfg = ModelConfig.from_json(config_path)
    tok = load_tokenizer(tokenizer_path)
    cfg.vocab_size = len(tok.vocab)
    dev = torch.device(
        device
        or (
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
    )
    model = OMTransformer(cfg).to(dev)
    if checkpoint:
        ck = torch.load(checkpoint, map_location=dev, weights_only=False)
        model.load_state_dict(ck.get("model", ck))
    return cfg, tok, model, dev


def model_info(args):
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


def sft(args):
    cfg, tok, model, dev = load_model(args.config, args.tokenizer, args.checkpoint, args.device)
    ds = SFTDataset(args.data, tok, cfg.max_seq_len)
    tc = SFTConfig(
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        output_dir=args.output,
        checkpoint_every=args.checkpoint_every,
    )
    print(json.dumps({"stage": "sft", "device": str(dev), "rows": len(ds), "parameters": model.exact_parameter_count()}))
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
    svc = CorpusService(output_dir=args.workdir)
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

    uvicorn.run("om_ai.api.main:app", host=args.host, port=args.port, reload=args.reload)


def main():
    p = argparse.ArgumentParser(prog="om-ai", description="OM AI Operating Brain CLI")
    sp = p.add_subparsers(dest="cmd", required=True)

    mi = sp.add_parser("model-info")
    mi.add_argument("--config", required=True)
    mi.add_argument("--tokenizer")
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

    e = sp.add_parser("evaluate")
    e.add_argument("--config", required=True)
    e.add_argument("--tokenizer", required=True)
    e.add_argument("--checkpoint", required=True)
    e.add_argument("--device")
    e.set_defaults(func=evaluate)

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

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
