# Vision

Packages: `om_ai/vision/` — `vit.py`, `base.py`, `multimodal.py`.

## What is implemented

- Trainable Vision Transformer-style encoder (`vit.py`)
- `MultimodalProjector` (LayerNorm → Linear → GELU → Linear) mapping vision dim → LLM dim
- `OMVisionLanguageModel`: encode images → project → feed `encoder_hidden_states` into `OMTransformer` with cross-attention

Requires LLM `ModelConfig.cross_attention=true`.

## Optional dependency

```bash
pip install -e '.[vision]'   # pillow
```

## What is not included

- Production VLM weights
- Large paired image–text datasets
- Claims of competitive VQA / captioning scores

Train on your licensed image–text data; evaluate with your suites; register checkpoints like any other model. Interfaces also allow swapping in a locally hosted vision backend via contracts in `vision/base.py` when you bring your own stack.
