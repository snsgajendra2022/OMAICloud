from __future__ import annotations
import math, re
import torch


class EvaluationHarness:
    def __init__(self, model, tokenizer, device=None):
        self.model=model
        self.tokenizer=tokenizer
        self.device=torch.device(device or next(model.parameters()).device)

    @torch.no_grad()
    def perplexity(self, texts: list[str]):
        losses=[]
        self.model.eval()
        for text in texts:
            ids=self.tokenizer.encode(text, add_bos=True, add_eos=True)
            if len(ids)<2: continue
            ids=ids[:self.model.cfg.max_seq_len]
            x=torch.tensor([ids[:-1]], device=self.device)
            y=torch.tensor([ids[1:]], device=self.device)
            losses.append(float(self.model(x, labels=y)['loss']))
        mean=sum(losses)/max(1,len(losses))
        return {'loss':mean,'perplexity':math.exp(min(20,mean))}

    @torch.no_grad()
    def complete(self, prompt, max_new_tokens=32):
        ids=self.tokenizer.encode(prompt, add_bos=True)
        x=torch.tensor([ids], device=self.device)
        out=self.model.generate(x,max_new_tokens=max_new_tokens,eos_token_id=self.tokenizer.eos_id)
        return self.tokenizer.decode(out[0].tolist())

    def smoke_suite(self):
        cases={
            'language':'The capital of France is',
            'reasoning':'If all birds have wings and a sparrow is a bird, then',
            'math':'2 + 2 =',
            'coding':'def add(a, b):',
            'tool_usage':'To call a calculator tool, I should',
        }
        return {name:self.complete(p,16) for name,p in cases.items()}
