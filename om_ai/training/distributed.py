from __future__ import annotations
import argparse, os
from dataclasses import asdict
from pathlib import Path
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.utils.data import DataLoader, DistributedSampler

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.training.trainer import TrainingConfig, build_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--data', required=True); ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--strategy', choices=['ddp','fsdp'], default='ddp'); ap.add_argument('--steps', type=int, default=1000)
    ap.add_argument('--batch-size', type=int, default=1); ap.add_argument('--lr', type=float, default=3e-4); ap.add_argument('--output', default='artifacts/checkpoints')
    args = ap.parse_args()

    dist.init_process_group(backend='nccl' if torch.cuda.is_available() else 'gloo')
    rank = dist.get_rank(); local_rank = int(os.environ.get('LOCAL_RANK', 0))
    if torch.cuda.is_available(): torch.cuda.set_device(local_rank)
    device = torch.device(f'cuda:{local_rank}' if torch.cuda.is_available() else 'cpu')

    cfg = ModelConfig.from_json(args.config)
    model = OMTransformer(cfg).to(device)
    model = DDP(model, device_ids=[local_rank] if device.type == 'cuda' else None) if args.strategy == 'ddp' else FSDP(model)
    tok = ByteBPETokenizer.load(args.tokenizer)
    ds = build_dataset(args.data, tok, cfg.max_seq_len)
    sampler = DistributedSampler(ds, shuffle=True)
    dl = DataLoader(ds, batch_size=args.batch_size, sampler=sampler)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    step = 0
    while step < args.steps:
        sampler.set_epoch(step)
        for x,y in dl:
            x,y=x.to(device),y.to(device)
            out=model(x, labels=y)
            out['loss'].backward(); opt.step(); opt.zero_grad(set_to_none=True)
            step += 1
            if rank == 0 and step % 10 == 0: print({'step':step,'loss':float(out['loss'])})
            if step >= args.steps: break
    if rank == 0:
        Path(args.output).mkdir(parents=True, exist_ok=True)
        raw = model.module if hasattr(model, 'module') else model
        torch.save({'model':raw.state_dict(),'model_config':asdict(cfg)}, Path(args.output)/'distributed-latest.pt')
    dist.destroy_process_group()

if __name__ == '__main__': main()
