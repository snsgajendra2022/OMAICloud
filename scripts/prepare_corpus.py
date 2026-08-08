from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from om_ai.data.pipeline import DatasetPipeline, DocumentRecord
from om_ai.data.governance import CorpusGovernance


def read_owned_source(uri: str) -> str:
    p = Path(uri)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Approved source is not a local file: {uri}")
    if p.suffix.lower() in {".txt", ".md", ".html", ".htm", ".csv", ".log", ".json"}:
        return p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix.lower() == ".jsonl":
        texts=[]
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip(): continue
            obj=json.loads(line)
            texts.append(str(obj.get("text", obj)))
        return "\n\n".join(texts)
    raise ValueError(f"Unsupported source type: {p.suffix}. Convert it to text/markdown/jsonl first.")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--audit", default="artifacts/corpus_audit.json")
    args=ap.parse_args()

    manifests=CorpusGovernance.load_manifest(args.manifest)
    pipeline=DatasetPipeline()
    raw=[]; audit=[]
    for src in manifests:
        text=read_owned_source(src.uri)
        rec=DocumentRecord(text=text, source=src.source_id, license=src.license, category=src.category, language=src.language, version=src.version)
        raw.append(rec)
        audit.append({"source_id":src.source_id,"uri":src.uri,"license":src.license,"owner":src.owner,"sha256":CorpusGovernance.sha256_file(src.uri),"bytes":Path(src.uri).stat().st_size})
    processed=pipeline.process(raw)
    pipeline.save_jsonl(processed,args.output)
    CorpusGovernance.write_audit(audit,args.audit)
    print(json.dumps({"approved_sources":len(manifests),"records_written":len(processed),"output":args.output,"audit":args.audit},indent=2))

if __name__ == "__main__": main()
