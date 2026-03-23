"""
models/personality_model.py

TransformerFusion (E12) — OCEAN personality prediction architecture.
Test accuracy: 0.9170 on ChaLearn First Impressions V2 (10,000 videos).

Inputs:
  audio  : WavLM embeddings   (768-dim)
  text   : RoBERTa embeddings (768-dim)
  visual : ResNet50 embeddings (2048-dim)

Output:
  5 OCEAN trait scores, each in [0.0, 1.0]
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class TransformerFusion(nn.Module):
    """
    6 cross-attention pairs + TransformerEncoder over 3 modality tokens.
    Best performing model — test accuracy 0.9170.
    """

    def __init__(self, proj_dim: int = 256, num_heads: int = 8,
                 ff_dim: int = 512, num_layers: int = 3, dropout: float = 0.3):
        super().__init__()
        D = proj_dim

        self.audio_proj  = self._proj(768,  D, dropout)
        self.text_proj   = self._proj(768,  D, dropout)
        self.visual_proj = self._proj(2048, D, dropout)

        def ca():
            return nn.MultiheadAttention(D, num_heads, dropout=dropout, batch_first=True)

        self.a_from_t = ca(); self.a_from_v = ca()
        self.t_from_a = ca(); self.t_from_v = ca()
        self.v_from_a = ca(); self.v_from_t = ca()

        self.norm_a = nn.LayerNorm(D)
        self.norm_t = nn.LayerNorm(D)
        self.norm_v = nn.LayerNorm(D)

        enc_layer = nn.TransformerEncoderLayer(
            d_model=D, nhead=num_heads, dim_feedforward=ff_dim,
            dropout=dropout, batch_first=True, norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(enc_layer, num_layers=num_layers)

        self.head = nn.Sequential(
            nn.Linear(D * 3, 256),
            nn.LayerNorm(256), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(256, 64), nn.GELU(),
            nn.Linear(64, 5), nn.Sigmoid(),
        )

    @staticmethod
    def _proj(in_d, out_d, drop):
        return nn.Sequential(
            nn.Linear(in_d, out_d), nn.LayerNorm(out_d), nn.GELU(), nn.Dropout(drop)
        )

    def _cross(self, module, query, key):
        q, kv = query.unsqueeze(1), key.unsqueeze(1)
        out, _ = module(q, kv, kv)
        return out.squeeze(1)

    def forward(self, audio, text, visual):
        audio  = F.normalize(audio,  p=2, dim=-1)
        text   = F.normalize(text,   p=2, dim=-1)
        visual = F.normalize(visual, p=2, dim=-1)

        a = self.audio_proj(audio)
        t = self.text_proj(text)
        v = self.visual_proj(visual)

        a_out = self.norm_a(a + self._cross(self.a_from_t, a, t) + self._cross(self.a_from_v, a, v))
        t_out = self.norm_t(t + self._cross(self.t_from_a, t, a) + self._cross(self.t_from_v, t, v))
        v_out = self.norm_v(v + self._cross(self.v_from_a, v, a) + self._cross(self.v_from_t, v, t))

        tokens = torch.stack([a_out, t_out, v_out], dim=1)
        tokens = self.transformer(tokens)
        fused  = tokens.reshape(tokens.size(0), -1)
        return self.head(fused)