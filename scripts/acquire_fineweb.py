from datasets import load_dataset
from pathlib import Path
import argparse
import hashlib
import json
import time

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="data/production-corpus/raw/fineweb.txt")
parser.add_argument("--max-bytes", type=int, default=100_000_000)
parser.add_argument("--config", default="sample-10BT")
args = parser.parse_args()

output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)

manifest_path = output.with_suffix(".manifest.json")

print("Loading FineWeb in streaming mode...")

ds = load_dataset(
    "HuggingFaceFW/fineweb",
    name=args.config,
    split="train",
    streaming=True,
)

written = 0
documents = 0
sha = hashlib.sha256()
started = time.time()

with output.open("w", encoding="utf-8") as f:
    for row in ds:
        text = str(row.get("text", "")).strip()

        if len(text) < 100:
            continue

        payload = text + "\n\n"
        raw = payload.encode("utf-8")

        if written + len(raw) > args.max_bytes:
            break

        f.write(payload)
        sha.update(raw)

        written += len(raw)
        documents += 1

        if documents % 1000 == 0:
            print({
                "documents": documents,
                "bytes": written,
                "mb": round(written / 1_000_000, 2),
            })

manifest = {
    "source": "HuggingFaceFW/fineweb",
    "config": args.config,
    "license": "odc-by",
    "documents": documents,
    "bytes": written,
    "sha256": sha.hexdigest(),
    "output": str(output),
    "created_at": time.time(),
}

manifest_path.write_text(
    json.dumps(manifest, indent=2),
    encoding="utf-8",
)

print(json.dumps(manifest, indent=2))
