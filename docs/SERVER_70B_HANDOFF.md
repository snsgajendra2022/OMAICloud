# OM-70B server handoff (Mac → GPU cluster)

**Honest split:** This Mac prepares code, tokenizer, configs, and a smoke corpus. It **cannot** finish real OM-70B training (no multi-GPU CUDA / DeepSpeed ZeRO-3 at 70B scale). Final pretrain runs on a **Linux CUDA server**. `om-ai serve` never starts 70B training.

Related: [`TRAINING_70B.md`](TRAINING_70B.md) (architecture + launcher semantics).

---

## 1. What is ready locally (this Mac)

| Asset | Relative path | Absolute path (this machine) | Notes |
|-------|---------------|------------------------------|-------|
| Repo / trainers | `.` | `/Users/gajendrarawat/Downloads/om-ai-operating-brain 3` | `om_ai/training/train_70b.py`, `deepspeed_train.py`, partition init |
| Smoke corpus (small) | `data/production-corpus/clean/fineweb-deduped.jsonl` | `.../data/production-corpus/clean/fineweb-deduped.jsonl` | **~101 MB** — too small for 70B preflight (`--min-data-bytes` default **1 GB**) |
| Local ≥1 GB FineWeb | `data/production-corpus/clean/fineweb-1gb.jsonl` | `.../data/production-corpus/clean/fineweb-1gb.jsonl` | **~1.27 GB** deduped JSONL (ODC-By FineWeb `sample-10BT`); satisfies preflight **data** gate locally; real training still needs far more tokens on the server |
| HF production tokenizer | `artifacts/tokenizer-production-65536.json` | `.../artifacts/tokenizer-production-65536.json` | HuggingFace `tokenizers` JSON, vocab **65536** |
| OM ByteBPE (smaller) | `artifacts/tokenizer-om-production.json` | `.../artifacts/tokenizer-om-production.json` | Native OM format, vocab **4096** — not 70B target vocab |
| Model shape | `configs/70b.json` | | ~70B-class layout (`d_model=8192`, 80 layers, …) |
| DeepSpeed ZeRO-3 | `configs/deepspeed_zero3.json` | | bf16 + ZeRO-3 + CPU optimizer offload |
| Gates | `configs/train_70b_gates.json` | | Promotion rules (do not claim frontier without metrics) |
| Shell launcher | `scripts/train_70b.sh` | | Preflight → `deepspeed … deepspeed_train.py` |
| Preflight script | `scripts/om70b_preflight.py` | | CUDA / DeepSpeed / data size / tokenizer checks |
| Pack helper | `scripts/pack_for_70b_server.sh` | | Tar/list upload set (skips huge checkpoints) |
| Env template | `.env.example` | | Includes `OM_AI_70B_*` and serve-after-train vars |

Optional local (not 70B): tiny longrun on MPS may still be running — see §7. That run uses `configs/tiny.json` (~3.3M params) and is **not** OM-70B.

---

## 2. What to copy to the server

### Required

1. **Code + packaging**
   - Entire git checkout **or** the tarball from `./scripts/pack_for_70b_server.sh`
   - Must include: `om_ai/`, `configs/`, `scripts/`, `pyproject.toml`, docs above
2. **Corpus** (production scale on server disk, not the 100 MB Mac smoke file alone)
   - Path on server e.g. `/data/om/corpus/` (file or directory of shards)
   - Prefer licensed FineWeb / your governed JSONL after `om-ai corpus …`
3. **Tokenizer matching `configs/70b.json` vocab (65536)**
   - Copy `artifacts/tokenizer-production-65536.json`
   - Or train/export OM ByteBPE at 65536 with chat specials (see §4)
4. **Configs + scripts**
   - `configs/70b.json`
   - `configs/deepspeed_zero3.json`
   - `configs/train_70b_gates.json`
   - `scripts/train_70b.sh`, `scripts/om70b_preflight.py`

### Do **not** need to upload for 70B train

- `.venv/` (recreate on Linux)
- `artifacts/checkpoints/**` (tiny/demo/local longrun — wrong scale)
- SQLite DBs, chat UI state, Ollama models
- Mac MPS checkpoints under `artifacts/checkpoints/om-local-longrun/`

### Quick pack on Mac

```bash
cd "/Users/gajendrarawat/Downloads/om-ai-operating-brain 3"
./scripts/pack_for_70b_server.sh            # writes artifacts/handoff/om70b-server-pack-*.tar.gz + MANIFEST
./scripts/pack_for_70b_server.sh --list     # dry-run paths only
# scp / rsync the tarball + separately sync a large corpus if not included
```

Default pack **includes** the ~100 MB smoke corpus and the 65536 HF tokenizer; it **excludes** checkpoint trees and `.venv`.

---

## 3. Server prerequisites

| Requirement | Guidance |
|-------------|----------|
| OS | Linux x86_64 (CUDA cluster / DGX / cloud GPU VM) |
| Python | ≥ 3.11 |
| CUDA + drivers | Matching installed PyTorch CUDA build |
| GPUs | Launcher defaults: **≥ 8× GPUs**, **≥ ~40 GB VRAM each** (`om-ai train-70b --min-gpus 8 --min-vram-gb 40`) |
| RAM / disk | Large host RAM for ZeRO-3 CPU offload; **≫ 500 GB free** recommended (`--min-free-gb 500`); corpus + checkpoints need multi-TB for real runs |
| DeepSpeed | `pip install -e '.[deepSpeed]'` → `deepspeed` on `PATH` |
| NCCL | Working multi-GPU interconnect |
| Data | Preflight script default: corpus **≥ 1 GB** (`scripts/om70b_preflight.py --min-data-bytes`); real capability needs far more tokens |

Mac / MPS / CPU cannot satisfy the CUDA+DeepSpeed ready gate. That is expected.

**Local data gate note:** The old `fineweb-deduped.jsonl` (~101 MB) fails preflight because the gate wants ≥1e9 bytes — tiny smoke corpora cannot claim ready. After expanding FineWeb (`scripts/acquire_fineweb.py` → `om-ai corpus dedupe`), `data/production-corpus/clean/fineweb-1gb.jsonl` is **≥ 1 GB** so `data.ok` can be true on this Mac; `cuda` / DeepSpeed remain false until a GPU cluster.

---

## 4. Tokenizer: HF vs OM ByteBPE

`om_ai.tokenizer.load_tokenizer(path)` accepts either:

1. **OM ByteBPE JSON** — top-level `vocab` + `merges` → `ByteBPETokenizer`
2. **HuggingFace tokenizers JSON** — top-level `model` → `HFTokenizerAdapter` (needs `pip install tokenizers`)

Production file on Mac:

- Relative: `artifacts/tokenizer-production-65536.json`
- Absolute: `/Users/gajendrarawat/Downloads/om-ai-operating-brain 3/artifacts/tokenizer-production-65536.json`

Chat specials required: `<system>`, `</system>`, `<user>`, `</user>`, `<assistant>`, `</assistant>` (plus pad/bos/eos/unk).

`scripts/om70b_preflight.py` may note HF format and remind you that some older paths assumed OM-only; **current** `deepspeed_train.py` / trainers call `load_tokenizer`, so HF works when `tokenizers` is installed. Prefer keeping one tokenizer for train **and** later `serve`.

Train a native OM 65536 tokenizer if you want ByteBPE-only:

```bash
om-ai tokenizer train \
  --input /data/om/corpus \
  --output /data/om/tokenizer-bytebpe-65536.json \
  --vocab-size 65536
om-ai tokenizer inspect --tokenizer /data/om/tokenizer-bytebpe-65536.json
```

---

## 5. Exact env exports and train commands (server)

```bash
cd /path/to/om-ai-operating-brain   # extracted pack or git clone
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e '.[deepSpeed]'       # pulls deepspeed; ensure CUDA torch matches cluster

# --- required for scripts/train_70b.sh ---
export OM_AI_70B_DATA=/data/om/corpus/licensed.jsonl          # ≥1GB; prefer much larger
export OM_AI_70B_TOKENIZER=/data/om/tokenizer-production-65536.json
export OM_AI_70B_CONFIG=configs/70b.json                      # optional; this is the default
export OM_AI_70B_DEEPSPEED=configs/deepspeed_zero3.json       # optional default
export OM_AI_70B_OUTPUT=/data/om/checkpoints/om-70b

# Preflight only (safe; exits non-zero if not ready)
python scripts/om70b_preflight.py \
  --config "$OM_AI_70B_CONFIG" \
  --data "$OM_AI_70B_DATA" \
  --tokenizer "$OM_AI_70B_TOKENIZER"

# Launch (preflight + DeepSpeed ZeRO-3)
./scripts/train_70b.sh
```

Equivalent CLI:

```bash
om-ai train-70b \
  --config configs/70b.json \
  --data "$OM_AI_70B_DATA" \
  --tokenizer "$OM_AI_70B_TOKENIZER" \
  --output "$OM_AI_70B_OUTPUT" \
  --deepspeed configs/deepspeed_zero3.json \
  --strategy deepspeed_zero3
```

Useful flags:

- `--preflight-only` — validate without training
- `--resume` — continue from status under `--output`
- `--min-gpus`, `--min-vram-gb`, `--min-free-gb`, `--min-corpus-bytes` — adjust gates for your cluster
- `--allow-cpu` — **dev only**; will not produce a real 70B brain

Status file written under output: `OM70B_TRAINING_STATUS.json`. DeepSpeed tags land under `$OM_AI_70B_OUTPUT` (see `LATEST_TAG.txt`).

---

## 6. Bring checkpoints back / point `serve` at them

After a real cluster run:

1. Sync checkpoint directory (and `LATEST_TAG.txt` / consolidated export your cluster uses) to the machine that will serve, e.g. `artifacts/checkpoints/om-70b/` or keep on networked storage.
2. Point serve at the **same** config + tokenizer used for training:

```bash
export OM_AI_CHAT_BACKEND=local
export OM_AI_AUTOLOAD=1
export OM_AI_CONFIG=configs/70b.json
export OM_AI_TOKENIZER=artifacts/tokenizer-production-65536.json   # or server path
export OM_AI_CHECKPOINT=/data/om/checkpoints/om-70b/<consolidated>.pt   # or your export path
om-ai serve --host 0.0.0.0 --port 8080
```

Notes:

- DeepSpeed `engine.save_checkpoint` writes a **ZeRO directory tree**, not always a single `.pt`. You may need a consolidate/export step for single-process `serve` (cluster-specific). Until consolidated, keep inference on the training stack or export weights explicitly.
- Do **not** point 70B `serve` at `artifacts/checkpoints/om-local-longrun/latest.pt` (tiny ~3.3M MPS run).
- Never set production / `trained=True` without passing gates in `configs/train_70b_gates.json` and your eval suites.

---

## 7. Optional: local tiny continue-while-waiting (Mac)

A **tiny** longrun may still be alive on this Mac (MPS). It is useful only for pipeline / chat-local experiments while the GPU cluster does real 70B work.

Check:

```bash
pgrep -fl 'om-ai train'
tail -n 20 artifacts/om-local-longrun-train.log
# PID file: artifacts/om-local-longrun.pid
# Status snapshot: artifacts/LOCAL_TRAINING_STATUS.json
```

As of handoff prep (2026-08-13): process was **alive** (`om-ai train` on `configs/tiny.json`, FineWeb smoke corpus, `artifacts/tokenizer-fixed-v3.json`, output `artifacts/checkpoints/om-local-longrun`, ~step 89k+, loss ~1.7). **`not_70b: true`**.

Point chat at tiny local weights (weak English vs Ollama):

```bash
export OM_AI_CHAT_BACKEND=local
export OM_AI_AUTOLOAD=1
export OM_AI_CONFIG=configs/tiny.json
export OM_AI_TOKENIZER=artifacts/tokenizer-fixed-v3.json
export OM_AI_CHECKPOINT=artifacts/checkpoints/om-local-longrun/latest.pt
```

---

## 8. First three commands on the server

After upload/extract and corpus + tokenizer paths are set:

```bash
cd /path/to/om-ai-operating-brain && python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[deepSpeed]'
export OM_AI_70B_DATA=/data/om/corpus/licensed.jsonl OM_AI_70B_TOKENIZER=/data/om/tokenizer-production-65536.json OM_AI_70B_OUTPUT=/data/om/checkpoints/om-70b
./scripts/train_70b.sh
```

(Replace `/data/om/...` with your mounts. Ensure the corpus is large enough for preflight before expecting a long train.)
