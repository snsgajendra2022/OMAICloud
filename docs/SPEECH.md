# Speech

Package: `om_ai/voice/` — `audio_encoder.py`, `base.py`.

## What is implemented

- `AudioFeatureExtractor` — STFT log-magnitude features
- `SpeechEncoder` — Transformer encoder over projected spectrogram frames
- `CTCASRModel` — linear CTC head over encoder states

Optional: `pip install -e '.[voice]'` (`soundfile`).

Backend contracts in `voice/base.py` cover ASR and TTS adapters. **TTS:** this release supplies the contract/interface, not a trained neural TTS stack.

## Multimodal wiring

`MultimodalOrchestrator` can call an ASR path when audio is present and an encoder is configured; otherwise it errors clearly.

## What is not included

- Production ASR weights
- Large speech corpora / transcripts
- Benchmark scores (WER/CER) for a finished OM speech model

Train CTC (or later seq2seq) on licensed audio; treat demo/smoke runs as wiring tests only.
