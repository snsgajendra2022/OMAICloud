from __future__ import annotations
import argparse, json
import torch
from torch.utils.data import DataLoader

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.training.trainer import build_dataset


def main():
    try:
        import deepspeed
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[deepSpeed]'") from exc
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--data', required=True); ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--deepspeed', required=True); ap.add_argument('--local_rank', type=int, default=-1)
    args = ap.parse_args()
    cfg = ModelConfig.from_json(args.config)
    model = OMTransformer(cfg)
    tok = ByteBPETokenizer.load(args.tokenizer)
    ds = build_dataset(args.data, tok, cfg.max_seq_len)
    ds_cfg = json.load(open(args.deepspeed))
    engine, _, loader, _ = deepspeed.initialize(model=model, model_parameters=model.parameters(), training_data=ds, config=ds_cfg)
    steps = int(ds_cfg.get('scheduler',{}).get('params',{}).get('total_num_steps', 1000))
    step=0
    for batch in loader:
        x,y=[z.to(engine.device) for z in batch]
        loss=engine(x, labels=y)['loss']
        engine.backward(loss); engine.step(); step+=1
        if engine.global_rank == 0 and step%10==0: print({'step':step,'loss':float(loss)})
        if step>=steps: break
    engine.save_checkpoint('artifacts/checkpoints/deepspeed')

if __name__ == '__main__': main()
