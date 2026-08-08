import json
from pathlib import Path
import torch
from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.training.sft import SFTDataset
from om_ai.training.preference import PreferenceDataset
from om_ai.training.dpo import sequence_logprob
from om_ai.training.reward_model import RewardModel


def test_sft_dpo_reward_shapes(tmp_path):
    tok=ByteBPETokenizer.base()
    sft=tmp_path/'sft.jsonl'; sft.write_text(json.dumps({'prompt':'Hi','response':'Hello'})+'\n')
    ds=SFTDataset(str(sft),tok,32); x,y=ds.collate([ds[0]])
    cfg=ModelConfig(vocab_size=len(tok.vocab),max_seq_len=32,n_layers=1,n_heads=4,d_model=32,d_ff=64)
    model=OMTransformer(cfg)
    assert model(x,labels=y)['loss'].ndim==0

    pref=tmp_path/'pref.jsonl'; pref.write_text(json.dumps({'prompt':'2+2','chosen':'4','rejected':'5'})+'\n')
    pds=PreferenceDataset(str(pref),tok,32); b=pds.collate([pds[0]])
    lp=sequence_logprob(model,b['chosen_ids'],b['chosen_mask']); assert lp.shape==(1,)
    rm=RewardModel(model); scores=rm(b['chosen_ids'],b['chosen_ids']!=tok.pad_id); assert scores.shape==(1,)
