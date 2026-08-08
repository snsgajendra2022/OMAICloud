from __future__ import annotations
"""One-machine demonstrator for the real training lifecycle. Scale the same stages with DDP/FSDP/DeepSpeed."""
import argparse, json, subprocess, sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def run(cmd):
    print("+", " ".join(cmd)); subprocess.run(cmd,check=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",default="configs/tiny.json");ap.add_argument("--pretrain-data",default="data/example_corpus.txt");ap.add_argument("--sft-data",default="data/example_sft.jsonl");ap.add_argument("--preference-data",default="data/example_preferences.jsonl");ap.add_argument("--steps",type=int,default=5);args=ap.parse_args()
    tok="artifacts/tokenizer.json";Path("artifacts").mkdir(exist_ok=True)
    run([sys.executable,"-m","om_ai.cli","tokenizer","train","--input",args.pretrain_data,"--output",tok,"--vocab-size","512"])
    run([sys.executable,"-m","om_ai.cli","train","--config",args.config,"--data",args.pretrain_data,"--tokenizer",tok,"--steps",str(args.steps),"--output","artifacts/pretrain","--checkpoint-every",str(args.steps)])
    run([sys.executable,"-m","om_ai.cli","sft","--config",args.config,"--data",args.sft_data,"--tokenizer",tok,"--checkpoint","artifacts/pretrain/latest.pt","--steps",str(args.steps)])
    run([sys.executable,"-m","om_ai.cli","dpo","--config",args.config,"--data",args.preference_data,"--tokenizer",tok,"--checkpoint","artifacts/sft/latest.pt","--steps",str(args.steps)])
    print(json.dumps({"complete":True,"final_checkpoint":"artifacts/dpo/latest.pt"},indent=2))
if __name__=="__main__":main()
