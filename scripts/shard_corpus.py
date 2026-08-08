from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--records-per-shard", type=int, default=10000)
    args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    shard=[]; index=0; total=0; paths=[]
    def flush(rows, idx):
        if not rows: return None
        p=out/f"shard-{idx:05d}.jsonl"
        p.write_text("\n".join(rows)+"\n", encoding="utf-8")
        return str(p)
    for line in Path(args.input).read_text(encoding="utf-8",errors="ignore").splitlines():
        if not line.strip(): continue
        json.loads(line)
        shard.append(line); total += 1
        if len(shard)>=args.records_per_shard:
            paths.append(flush(shard,index)); index+=1; shard=[]
    p=flush(shard,index)
    if p: paths.append(p)
    print(json.dumps({"records":total,"shards":len(paths),"paths":paths},indent=2))
if __name__ == "__main__": main()
