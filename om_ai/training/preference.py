from __future__ import annotations
from pathlib import Path
import json
import torch
from torch.utils.data import Dataset

class PreferenceDataset(Dataset):
    """JSONL: {prompt, chosen, rejected}."""
    def __init__(self,path,tokenizer,max_seq_len):
        self.rows=[]; self.tok=tokenizer; self.max_seq_len=max_seq_len
        for line in Path(path).read_text(encoding="utf-8",errors="ignore").splitlines():
            if not line.strip(): continue
            obj=json.loads(line); prompt=str(obj["prompt"]); chosen=str(obj["chosen"]); rejected=str(obj["rejected"])
            self.rows.append((prompt,chosen,rejected))
        if not self.rows: raise ValueError("No preference rows")

    def __len__(self): return len(self.rows)
    def __getitem__(self,i): return self.rows[i]

    def encode_pair(self, prompt, response):
        """Encode prompt/response with the same chat specials as SFT/inference."""
        messages = [{"role": "user", "content": prompt}]
        if self.tok.inspect().get("chat_tokens_available"):
            prefix = self.tok.encode_chat(messages, add_generation_prompt=True)
            full = self.tok.encode_chat(
                messages + [{"role": "assistant", "content": response}],
                add_generation_prompt=False,
                add_eos=True,
            )
            if full[: len(prefix)] != prefix:
                raise ValueError(
                    "Preference chat encoding mismatch: generation prompt is "
                    "not a prefix of the completed dialogue encoding."
                )
            ids = full[: self.max_seq_len]
            response_start = min(len(prefix), len(ids))
        else:
            # Legacy vocab fallback (byte-encodes angle brackets — avoid for new runs).
            pids = self.tok.encode(
                f"<user>\n{prompt}\n</user>\n<assistant>\n", add_bos=True
            )
            rids = self.tok.encode(response + "\n</assistant>", add_eos=True)
            ids = (pids + rids)[: self.max_seq_len]
            response_start = min(len(pids), len(ids))
        mask = [0] * response_start + [1] * max(0, len(ids) - response_start)
        return ids, mask

    def collate(self,batch):
        enc=[]
        for prompt,chosen,rejected in batch:
            enc.append((self.encode_pair(prompt,chosen),self.encode_pair(prompt,rejected)))
        maxlen=max(max(len(c[0]),len(r[0])) for c,r in enc)
        def pad(item):
            ids,mask=item; n=maxlen-len(ids)
            return ids+[self.tok.pad_id]*n, mask+[0]*n
        cids=[];cm=[];rids=[];rm=[]
        for c,r in enc:
            a,b=pad(c); d,e=pad(r); cids.append(a);cm.append(b);rids.append(d);rm.append(e)
        return {"chosen_ids":torch.tensor(cids),"chosen_mask":torch.tensor(cm,dtype=torch.float32),"rejected_ids":torch.tensor(rids),"rejected_mask":torch.tensor(rm,dtype=torch.float32)}
