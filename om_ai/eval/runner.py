from __future__ import annotations
from pathlib import Path
import json, re, time

class BenchmarkRunner:
    def __init__(self,harness): self.harness=harness
    def run(self,path:str,report_path:str|None=None,max_new_tokens:int=64):
        rows=[]; passed=0
        for line in Path(path).read_text(encoding="utf-8",errors="ignore").splitlines():
            if not line.strip(): continue
            case=json.loads(line); prompt=case["prompt"]; out=self.harness.complete(prompt,max_new_tokens=max_new_tokens)
            answer=out[len(prompt):] if out.startswith(prompt) else out
            mode=case.get("metric","contains"); expected=str(case.get("expected",""))
            if mode=="exact": ok=answer.strip()==expected.strip()
            elif mode=="regex": ok=re.search(expected,answer,re.I|re.S) is not None
            else: ok=expected.lower() in answer.lower()
            passed += int(ok); rows.append({"id":case.get("id"),"category":case.get("category"),"prompt":prompt,"expected":expected,"output":answer,"passed":ok})
        result={"generated_at":time.time(),"total":len(rows),"passed":passed,"accuracy":passed/max(1,len(rows)),"cases":rows}
        if report_path:
            p=Path(report_path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2,ensure_ascii=False))
        return result
