import torch
from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer

def test_forward_and_cache():
    cfg=ModelConfig(vocab_size=300,max_seq_len=32,n_layers=2,n_heads=4,d_model=64,d_ff=128)
    m=OMTransformer(cfg)
    x=torch.randint(0,300,(2,8)); y=torch.randint(0,300,(2,8))
    out=m(x,labels=y,use_cache=True)
    assert out['logits'].shape==(2,8,300)
    assert out['loss'].ndim==0
    nxt=torch.randint(0,300,(2,1))
    out2=m(nxt,caches=out['caches'],use_cache=True)
    assert out2['logits'].shape==(2,1,300)


def test_optional_cross_attention():
    cfg=ModelConfig(vocab_size=128,max_seq_len=16,n_layers=1,n_heads=4,d_model=32,d_ff=64,cross_attention=True)
    m=OMTransformer(cfg)
    x=torch.randint(0,128,(1,4))
    context=torch.randn(1,3,32)
    out=m(x,encoder_hidden_states=context)
    assert out["logits"].shape==(1,4,128)
