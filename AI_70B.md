Yes. Improve it progressively, but treat “better brain” and “bigger model” as two separate things.

Your current trainer already cycles through the dataset when it reaches the end, supports checkpoint resume, AdamW, cosine LR, gradient clipping, and MPS. Your train-om1 command also saves latest.pt, tokenizer fingerprints, metadata, and registry information.

One important correction: your om-1.0-local.json has max_seq_len=128. Therefore:

1000 steps × batch 2 × 128 tokens
≈ 256,000 token positions

So --max-tokens 5000000 does not mean five million tokens are actually trained. It only sets the maximum dataset material available to the trainer.

Use this progression.

Stage 1 — verify OM-1.0 training properly. Start with 1,000 steps:
om-ai train-om1 \
  --config configs/om-1.0-local.json \
  --data data/production-corpus/raw/fineweb-100mb.txt \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --steps 1000 \
  --batch-size 4 \
  --max-tokens 5000000 \
  --max-docs 50000 \
  --checkpoint-every 100 \
  --log-every 10 \
  --device mps \
  --precision auto \
  --output artifacts/checkpoints/om-1.0-base

For sequence length 128 and batch 4, that's roughly:

1000 × 4 × 128
≈ 512,000 token positions

The goal here is not intelligence. Confirm:

loss finite
loss generally decreases
no MPS crash
latest.pt created
checkpoint reloads
Stage 2 — continue the exact same OM model instead of restarting. Once Stage 1 works, resume it to 5,000 total steps:
om-ai train-om1 \
  --config configs/om-1.0-local.json \
  --data data/production-corpus/raw/fineweb-100mb.txt \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --steps 5000 \
  --batch-size 4 \
  --max-tokens 10000000 \
  --max-docs 100000 \
  --checkpoint-every 500 \
  --log-every 25 \
  --device mps \
  --precision auto \
  --resume artifacts/checkpoints/om-1.0-base/latest.pt \
  --output artifacts/checkpoints/om-1.0-base

Because your trainer restores global_step, --steps 5000 means continue until total step 5,000, not add another 5,000.

At this point the approximate training exposure becomes:

5000 × 4 × 128
≈ 2.56 million token positions
Stage 3 — continue to 20,000 steps.
om-ai train-om1 \
  --config configs/om-1.0-local.json \
  --data data/production-corpus/raw/fineweb-100mb.txt \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --steps 20000 \
  --batch-size 4 \
  --max-tokens 25000000 \
  --max-docs 250000 \
  --checkpoint-every 1000 \
  --log-every 50 \
  --device mps \
  --precision auto \
  --resume artifacts/checkpoints/om-1.0-base/latest.pt \
  --output artifacts/checkpoints/om-1.0-base

That's roughly:

20,000 × 4 × 128
≈ 10.24 million token positions

But don't blindly keep repeating the same 100 MB forever. Once loss stops improving meaningfully, increase data quality/diversity instead of merely adding steps.

Stage 4 — stop base pretraining temporarily and teach OM how to answer. Base text prediction alone won't make a good chat assistant. Create a high-quality SFT dataset and train from the base checkpoint:
om-ai sft \
  --config configs/om-1.0-local.json \
  --data data/om-sft.jsonl \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/om-1.0-base/latest.pt \
  --steps 5000 \
  --batch-size 2 \
  --lr 2e-5 \
  --checkpoint-every 500 \
  --output artifacts/checkpoints/om-1.0-sft \
  --device mps

This is where you teach things like:

follow instructions
answer clearly
coding style
reasoning format
OM identity
tool usage
project assistance
question answering
Stage 5 — improve answers using your own feedback. Your CLI already has feedback export and DPO support. Export good/bad responses:
om-ai feedback export \
  --db artifacts/feedback.sqlite3 \
  --sft-output data/om-feedback-sft.jsonl \
  --preference-output data/om-feedback-preferences.jsonl \
  --min-rating 4

Then preference-train:

om-ai dpo \
  --config configs/om-1.0-local.json \
  --data data/om-feedback-preferences.jsonl \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/om-1.0-sft/latest.pt \
  --steps 1000 \
  --batch-size 2 \
  --lr 1e-6 \
  --output artifacts/checkpoints/om-1.0-dpo \
  --device mps

This progression is much better than simply doing:

1000 → 10000 → 100000 steps

on the same web corpus.

Stage 6 — increase the actual OM architecture. This is where the distinction becomes important.

Do not do this:

OM-small checkpoint
 ↓
change config to 1B
 ↓
resume checkpoint

That fails because tensor dimensions/layer counts differ.

Instead:

OM local small model
       ↓
prove tokenizer/data/trainer/SFT/DPO
       ↓
OM-100M new architecture → train from scratch
       ↓
OM-300M new architecture → train from scratch
       ↓
OM-1B new architecture → train from scratch
       ↓
OM-7B new architecture → train from scratch
       ↓
OM-13B new architecture → train from scratch
       ↓
OM-70B new architecture → train from scratch

You can reuse the same production tokenizer, corpus pipeline, cleaned datasets, SFT datasets, preference datasets, tests and runtime, but normally not the smaller model weights.

Your repo already has a 7B architecture with 32 layers, hidden size 4096 and 8192 context. It also already has dedicated 1B/7B/13B/70B configs and a separate train-70b command.

Stage 7 — final 70B path. Eventually the workflow becomes:
OM-1.0 local
   ↓
pipeline proven
   ↓
larger licensed/approved corpus
   ↓
production 65,536 tokenizer
   ↓
100M/300M experiments
   ↓
1B experiment
   ↓
7B experiment
   ↓
13B experiment
   ↓
70B preflight
   ↓
70B distributed pretraining
   ↓
70B SFT
   ↓
70B preference training
   ↓
70B evaluation
   ↓
OM-70B production checkpoint

And your repository's final 70B command is structurally:

om-ai train-70b \
  --config configs/70b.json \
  --data /path/to/full-production-corpus \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --output artifacts/checkpoints/om-70b \
  --strategy deepspeed_zero3 \
  --pretrain-steps 1000

But do not run that final command on your current Mac expecting real 70B training. Your train-70b command itself has checks for multiple GPUs, VRAM, free storage and corpus size; the CLI even labels --allow-cpu as development-only and says it will not produce a real 70B brain.

What I recommend you run now

Your immediate improved command should be Stage 1, not 70B:

om-ai train-om1 \
  --config configs/om-1.0-local.json \
  --data data/production-corpus/raw/fineweb-100mb.txt \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --steps 1000 \
  --batch-size 4 \
  --max-tokens 5000000 \
  --max-docs 50000 \
  --checkpoint-every 100 \
  --log-every 10 \
  --device mps \
  --precision auto \
  --output artifacts/checkpoints/om-1.0-base

Then inspect the loss output. If that passes, move to 5,000 with --resume. That is the correct first step toward progressively improving your own OM brain.