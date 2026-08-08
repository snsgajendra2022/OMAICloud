from pathlib import Path
import tempfile
import torch
from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.data import DatasetPipeline

text='OM AI learns from private data. OM AI reasons and acts safely.'
tok=ByteBPETokenizer.train([text],vocab_size=300,min_pair_freq=1)
cfg=ModelConfig(vocab_size=len(tok.vocab),max_seq_len=64,n_layers=2,n_heads=4,d_model=64,d_ff=128)
model=OMTransformer(cfg)
ids=tok.encode(text,add_bos=True,add_eos=True)[:32]
x=torch.tensor([ids[:-1]]); y=torch.tensor([ids[1:]])
out=model(x,labels=y)
assert torch.isfinite(out['loss'])
g=model.generate(x[:,:4],max_new_tokens=3,temperature=0)
assert g.shape[1]==7
print({'ok':True,'parameters':model.exact_parameter_count(),'loss':float(out['loss'].detach())})
