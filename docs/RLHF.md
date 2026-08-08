# RLHF Path (Reward Model + PPO)

OM AI supports a classical RLHF-style stack in software. Running it to production quality still needs preference data, rollouts, and compute.

## Components

| Stage | Module | CLI / API |
|-------|--------|-----------|
| Preference pairs | `om_ai/training/preference.py` | Shared with DPO |
| Pairwise reward model | `om_ai/training/reward_model.py` | `om-ai reward` |
| PPO (GAE, clipped surrogate, KL to ref) | `om_ai/training/ppo.py` | Library / training scripts |

## Reward model

Bradley-Terry / log-sigmoid pairwise training over (chosen, rejected) pairs atop an `OMTransformer` backbone wrapped by `RewardModel`.

```bash
om-ai reward \
  --config configs/tiny.json \
  --data data/example_preferences.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/sft/latest.pt \
  --steps 500 \
  --output artifacts/reward
```

## PPO infrastructure

`om_ai/training/ppo.py` provides:

- `Rollout` / `RolloutBuffer`
- GAE advantages
- Clipped policy surrogate + value loss + entropy bonus
- KL penalty vs reference policy

**Requirements:** a trained policy checkpoint, a reward scorer, and rollout generation. Short toy loops validate wiring; they do not prove human-level alignment.

## DPO vs RLHF

- **DPO** (`dpo.py`): simpler; no RM/PPO loop; good default for many preference sets
- **RLHF**: more moving parts; use when you need online reward optimization

## Honesty

No claim is made that PPO has been run at 7B/70B scale in this package. Infrastructure ≠ completed RLHF campaign.
