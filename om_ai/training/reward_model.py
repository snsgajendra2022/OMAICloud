from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from .preference import PreferenceDataset

class RewardModel(nn.Module):
    def __init__(self, backbone):
        super().__init__(); self.backbone=backbone; self.head=nn.Linear(backbone.cfg.d_model,1)
    def forward(self,ids,attention_mask=None):
        out=self.backbone(ids,output_hidden_states=True); h=out["hidden_states"]
        if attention_mask is None: idx=torch.full((ids.size(0),),ids.size(1)-1,device=ids.device,dtype=torch.long)
        else: idx=attention_mask.long().sum(-1).clamp_min(1)-1
        pooled=h[torch.arange(ids.size(0),device=ids.device),idx]
        return self.head(pooled).squeeze(-1)

@dataclass(slots=True)
class RewardConfig:
    steps:int=500
    batch_size:int=2
    learning_rate:float=1e-5
    output_dir:str="artifacts/reward"

class RewardTrainer:
    def __init__(self,model:RewardModel,dataset:PreferenceDataset,cfg:RewardConfig,device=None):
        self.model=model;self.ds=dataset;self.cfg=cfg;self.device=torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"));self.model.to(self.device);self.opt=torch.optim.AdamW(self.model.parameters(),lr=cfg.learning_rate)
    def train(self):
        loader=DataLoader(self.ds,batch_size=self.cfg.batch_size,shuffle=True,collate_fn=self.ds.collate);it=iter(loader);last=0.0
        for step in range(1,self.cfg.steps+1):
            try:b=next(it)
            except StopIteration:it=iter(loader);b=next(it)
            b={k:v.to(self.device) for k,v in b.items()}; cm=(b["chosen_ids"]!=self.ds.tok.pad_id);rm=(b["rejected_ids"]!=self.ds.tok.pad_id)
            cr=self.model(b["chosen_ids"],cm); rr=self.model(b["rejected_ids"],rm);loss=-F.logsigmoid(cr-rr).mean()
            self.opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(self.model.parameters(),1.0);self.opt.step();last=float(loss.detach())
            if step==1 or step%10==0: print(json.dumps({"stage":"reward","step":step,"loss":round(last,5),"pair_accuracy":round(float((cr>rr).float().mean()),4)}))
        p=Path(self.cfg.output_dir);p.mkdir(parents=True,exist_ok=True);target=p/"latest.pt";torch.save({"model":self.model.state_dict(),"stage":"reward","steps":self.cfg.steps},target);return {"checkpoint":str(target),"last_loss":last}
