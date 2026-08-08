from __future__ import annotations
from pathlib import Path
import json

def build_sft_replay(store,path,min_rating=4):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);count=0
    with p.open("w",encoding="utf-8") as f:
        for _,_,_,prompt,response,rating,preferred,_ in store.rows(min_rating):
            target=preferred or response
            f.write(json.dumps({"prompt":prompt,"response":target,"source":"feedback","rating":rating},ensure_ascii=False)+"\n");count+=1
    return count

def build_preference_replay(store,path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);count=0
    with p.open("w",encoding="utf-8") as f:
        for _,_,_,prompt,response,rating,preferred,_ in store.rows():
            if preferred and preferred.strip()!=response.strip():
                f.write(json.dumps({"prompt":prompt,"chosen":preferred,"rejected":response,"source":"feedback","rating":rating},ensure_ascii=False)+"\n");count+=1
    return count
