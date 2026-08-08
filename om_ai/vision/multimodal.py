from __future__ import annotations
import torch
import torch.nn as nn

class MultimodalProjector(nn.Module):
    def __init__(self,vision_dim:int,llm_dim:int):
        super().__init__();self.net=nn.Sequential(nn.LayerNorm(vision_dim),nn.Linear(vision_dim,llm_dim),nn.GELU(),nn.Linear(llm_dim,llm_dim))
    def forward(self,x): return self.net(x)

class OMVisionLanguageModel(nn.Module):
    def __init__(self,vision_encoder,projector,llm):
        super().__init__();self.vision_encoder=vision_encoder;self.projector=projector;self.llm=llm
        if not llm.cfg.cross_attention: raise ValueError("LLM config must set cross_attention=true")
    def forward(self,images,input_ids,labels=None):
        context=self.projector(self.vision_encoder(images));return self.llm(input_ids,labels=labels,encoder_hidden_states=context)
    @torch.no_grad()
    def generate(self,images,input_ids,**kwargs):
        context=self.projector(self.vision_encoder(images));return self.llm.generate(input_ids,encoder_hidden_states=context,**kwargs)
