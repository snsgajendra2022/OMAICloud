import torch
from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.vision import VisionTransformerEncoder, MultimodalProjector, OMVisionLanguageModel
from om_ai.voice import AudioFeatureExtractor, SpeechEncoder, CTCASRModel


def test_vision_language_forward():
    cfg=ModelConfig(vocab_size=128,max_seq_len=16,n_layers=1,n_heads=4,d_model=32,d_ff=64,cross_attention=True)
    llm=OMTransformer(cfg); vision=VisionTransformerEncoder(image_size=32,patch_size=8,d_model=32,layers=1,heads=4)
    vlm=OMVisionLanguageModel(vision,MultimodalProjector(32,32),llm)
    out=vlm(torch.randn(1,3,32,32),torch.randint(0,128,(1,5)))
    assert out['logits'].shape==(1,5,128)


def test_audio_encoder_forward():
    feat=AudioFeatureExtractor(n_fft=64,hop_length=32)(torch.randn(1,320))
    enc=SpeechEncoder(input_bins=33,d_model=32,layers=1,heads=4)
    model=CTCASRModel(enc,50); logits=model(feat)
    assert logits.shape[0]==1 and logits.shape[-1]==50
