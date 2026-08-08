from __future__ import annotations
import torch
import torch.nn as nn

class VisionTransformerEncoder(nn.Module):
    """Trainable image encoder. Produces patch tokens for OM decoder cross-attention."""
    def __init__(self,image_size=224,patch_size=16,in_channels=3,d_model=512,layers=6,heads=8,dropout=0.0):
        super().__init__(); assert image_size%patch_size==0
        self.image_size=image_size;self.patch_size=patch_size;self.d_model=d_model
        self.patch=nn.Conv2d(in_channels,d_model,kernel_size=patch_size,stride=patch_size)
        n=(image_size//patch_size)**2
        self.cls=nn.Parameter(torch.zeros(1,1,d_model));self.pos=nn.Parameter(torch.zeros(1,n+1,d_model))
        enc=nn.TransformerEncoderLayer(d_model,heads,dim_feedforward=4*d_model,batch_first=True,norm_first=True,dropout=dropout,activation="gelu")
        self.encoder=nn.TransformerEncoder(enc,layers);self.norm=nn.LayerNorm(d_model)
        nn.init.normal_(self.pos,std=.02);nn.init.normal_(self.cls,std=.02)
    def forward(self,images):
        x=self.patch(images).flatten(2).transpose(1,2);cls=self.cls.expand(images.size(0),-1,-1);x=torch.cat([cls,x],1);x=x+self.pos[:,:x.size(1)];return self.norm(self.encoder(x))
