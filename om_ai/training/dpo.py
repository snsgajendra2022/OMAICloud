from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import copy, json
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader


def sequence_logprob(model, ids:torch.Tensor, completion_mask:torch.Tensor):
    x=ids[:,:-1]; targets=ids[:,1:]; mask=completion_mask[:,1:]
    logits=model(x)["logits"]
    token_lp=F.log_softmax(logits,dim=-1).gather(-1,targets.unsqueeze(-1)).squeeze(-1)
    token_lp=token_lp*mask
    return token_lp.sum(-1) / mask.sum(-1).clamp_min(1.0)

@dataclass(slots=True)
class DPOConfig:
    steps:int=500
    batch_size:int=2
    learning_rate:float=1e-6
    beta:float=0.1
    output_dir:str="artifacts/dpo"

class DPOTrainer:
    def __init__(self,policy,dataset,cfg:DPOConfig,device=None,reference=None):
        self.policy=policy; self.ds=dataset; self.cfg=cfg
        self.device=torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.policy.to(self.device)
        self.reference=reference or copy.deepcopy(policy)
        self.reference.to(self.device).eval()
        for p in self.reference.parameters(): p.requires_grad_(False)
        self.opt=torch.optim.AdamW(self.policy.parameters(),lr=cfg.learning_rate)

    def train(self):
        loader=DataLoader(self.ds,batch_size=self.cfg.batch_size,shuffle=True,collate_fn=self.ds.collate)
        it=iter(loader); last=0.0
        self.policy.train()
        for step in range(1,self.cfg.steps+1):
            try:b=next(it)
            except StopIteration:it=iter(loader);b=next(it)
            b={k:v.to(self.device) for k,v in b.items()}
            pc=sequence_logprob(self.policy,b["chosen_ids"],b["chosen_mask"]); pr=sequence_logprob(self.policy,b["rejected_ids"],b["rejected_mask"])
            with torch.no_grad():
                rc=sequence_logprob(self.reference,b["chosen_ids"],b["chosen_mask"]); rr=sequence_logprob(self.reference,b["rejected_ids"],b["rejected_mask"])
            logits=self.cfg.beta*((pc-pr)-(rc-rr))
            loss=-F.logsigmoid(logits).mean()
            self.opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(self.policy.parameters(),1.0);self.opt.step()
            last=float(loss.detach())
            if step==1 or step%10==0: print(json.dumps({"stage":"dpo","step":step,"loss":round(last,5),"pref_accuracy":round(float((logits>0).float().mean()),4)}))
        p=Path(self.cfg.output_dir);p.mkdir(parents=True,exist_ok=True);target=p/"latest.pt"
        torch.save({"model":self.policy.state_dict(),"stage":"dpo","steps":self.cfg.steps,"beta":self.cfg.beta},target)
        return {"checkpoint":str(target),"steps":self.cfg.steps,"last_loss":last}
