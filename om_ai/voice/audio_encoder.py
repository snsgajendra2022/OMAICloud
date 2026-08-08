from __future__ import annotations
import torch
import torch.nn as nn

class AudioFeatureExtractor(nn.Module):
    def __init__(self,n_fft=400,hop_length=160): super().__init__();self.n_fft=n_fft;self.hop_length=hop_length
    def forward(self,waveform):
        if waveform.dim()==1: waveform=waveform.unsqueeze(0)
        win=torch.hann_window(self.n_fft,device=waveform.device)
        spec=torch.stft(waveform,n_fft=self.n_fft,hop_length=self.hop_length,window=win,return_complex=True).abs().clamp_min(1e-5).log()
        return spec.transpose(1,2)

class SpeechEncoder(nn.Module):
    """Trainable local speech encoder for cross-attention or CTC-style ASR heads."""
    def __init__(self,input_bins=201,d_model=512,layers=6,heads=8):
        super().__init__();self.proj=nn.Linear(input_bins,d_model);enc=nn.TransformerEncoderLayer(d_model,heads,4*d_model,batch_first=True,norm_first=True);self.encoder=nn.TransformerEncoder(enc,layers);self.norm=nn.LayerNorm(d_model)
    def forward(self,features): return self.norm(self.encoder(self.proj(features)))

class CTCASRModel(nn.Module):
    def __init__(self,encoder:SpeechEncoder,vocab_size:int): super().__init__();self.encoder=encoder;self.head=nn.Linear(encoder.norm.normalized_shape[0],vocab_size)
    def forward(self,features): return self.head(self.encoder(features))
