"""
ET-TACFN — Enhanced Trimodal Adaptive Cross-Modal Fusion Network
================================================================
Retrained model (April 2026):
  d_model:          256
  num_heads:        8
  dropout:          0.3
  num_classes:      4  (Happy, Sad, Angry, Neutral)
  text_input_dim:   768   ← RoBERTa-base
  audio_input_dim:  768   ← WavLM-base
  visual_input_dim: 2048  ← ResNet50 avgpool (raw, no projection)
"""

import os
import random

import torch
import torch.nn as nn


# ============================================================
#  BUILDING BLOCKS
# ============================================================

class ModalityProjector(nn.Module):
    def __init__(self, input_dim, d_model=256, dropout=0.1):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(input_dim, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )
    def forward(self, x):
        return self.proj(x)


class CrossModalAttention(nn.Module):
    def __init__(self, d_model=256, num_heads=8, dropout=0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(
            embed_dim=d_model, num_heads=num_heads,
            dropout=dropout, batch_first=True
        )
        self.norm1   = nn.LayerNorm(d_model)
        self.norm2   = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4), nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model), nn.Dropout(dropout)
        )

    def forward(self, query_mod, kv_mod, key_mask=None, need_weights=True):
        attended, attn_weights = self.attn(
            query=query_mod, key=kv_mod, value=kv_mod,
            key_padding_mask=key_mask,
            need_weights=need_weights, average_attn_weights=False
        )
        x = self.norm1(query_mod + self.dropout(attended))
        x = self.norm2(x + self.ffn(x))
        return x, attn_weights


class IntraModalSelfAttention(nn.Module):
    def __init__(self, d_model=256, num_heads=8, dropout=0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(
            embed_dim=d_model, num_heads=num_heads,
            dropout=dropout, batch_first=True
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4), nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model), nn.Dropout(dropout)
        )

    def forward(self, x, mask=None):
        attn_out, _ = self.self_attn(
            query=x, key=x, value=x,
            key_padding_mask=mask,
            need_weights=not self.training
        )
        x = self.norm1(x + self.dropout(attn_out))
        return self.norm2(x + self.ffn(x))


class TrimodalIntraAttention(nn.Module):
    def __init__(self, d_model=256, num_heads=8, dropout=0.1):
        super().__init__()
        self.text_self_attn   = IntraModalSelfAttention(d_model, num_heads, dropout)
        self.audio_self_attn  = IntraModalSelfAttention(d_model, num_heads, dropout)
        self.visual_self_attn = IntraModalSelfAttention(d_model, num_heads, dropout)

    def forward(self, text, audio, visual, text_mask=None, audio_mask=None, visual_mask=None):
        return (
            self.text_self_attn(text, text_mask),
            self.audio_self_attn(audio, audio_mask),
            self.visual_self_attn(visual, visual_mask),
        )


class HierarchicalFusion(nn.Module):
    def __init__(self, d_model=256, num_heads=8, dropout=0.1):
        super().__init__()
        self.cma_text_audio   = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_audio_text   = CrossModalAttention(d_model, num_heads, dropout)
        self.speech_combiner  = nn.Sequential(
            nn.Linear(d_model * 2, d_model), nn.LayerNorm(d_model),
            nn.GELU(), nn.Dropout(dropout)
        )
        self.cma_speech_visual = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_visual_speech = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_audio_visual  = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_visual_audio  = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_text_visual   = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_visual_text   = CrossModalAttention(d_model, num_heads, dropout)
        self.final_combiner    = nn.Sequential(
            nn.Linear(d_model * 2, d_model), nn.LayerNorm(d_model),
            nn.GELU(), nn.Dropout(dropout)
        )

    def _mean_pool(self, x, mask=None):
        if mask is not None:
            valid = (~mask).float().unsqueeze(-1)
            return (x * valid).sum(dim=1) / valid.sum(dim=1).clamp(min=1e-9)
        return x.mean(dim=1)

    def forward(self, text, audio, visual, text_mask=None, audio_mask=None, visual_mask=None):
        ta, w_ta = self.cma_text_audio(text,   audio,  audio_mask)
        at, w_at = self.cma_audio_text(audio,  text,   text_mask)
        tv, w_tv = self.cma_text_visual(text,  visual, visual_mask)
        av, w_av = self.cma_audio_visual(audio, visual, visual_mask)

        t_pool = self._mean_pool(ta + tv, text_mask)
        a_pool = self._mean_pool(at + av, audio_mask)
        speech = self.speech_combiner(torch.cat([t_pool, a_pool], dim=-1))

        speech_seq = speech.unsqueeze(1).expand(-1, visual.size(1), -1).contiguous()
        sv, w_sv = self.cma_speech_visual(speech_seq, visual, visual_mask)
        vs, w_vs = self.cma_visual_speech(visual, speech_seq, None)
        vt, w_vt = self.cma_visual_text(visual, text, text_mask)
        va, w_va = self.cma_visual_audio(visual, audio, audio_mask)

        sv_pool = self._mean_pool(sv, visual_mask)
        vs_pool = self._mean_pool(vs + vt + va, visual_mask)
        fused   = self.final_combiner(torch.cat([sv_pool, vs_pool], dim=-1))

        attn_weights = {
            "text_audio": w_ta, "audio_text": w_at,
            "text_visual": w_tv, "audio_visual": w_av,
            "speech_visual": w_sv, "visual_speech": w_vs,
            "visual_text": w_vt, "visual_audio": w_va,
        }
        return fused, speech, t_pool, a_pool, attn_weights


class ConfidenceGate(nn.Module):
    def __init__(self, d_model=256):
        super().__init__()
        self.gate_net = nn.Sequential(
            nn.Linear(d_model, d_model // 4), nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 4, 1), nn.Sigmoid()
        )
    def forward(self, x_pooled):
        return self.gate_net(x_pooled)


class TrimodalConfidenceGating(nn.Module):
    def __init__(self, d_model=256):
        super().__init__()
        self.gate_text   = ConfidenceGate(d_model)
        self.gate_audio  = ConfidenceGate(d_model)
        self.gate_visual = ConfidenceGate(d_model)

    def forward(self, text_feat, audio_feat, visual_feat):
        conf_t = self.gate_text(text_feat)
        conf_a = self.gate_audio(audio_feat)
        conf_v = self.gate_visual(visual_feat)
        return (
            conf_t * text_feat, conf_a * audio_feat, conf_v * visual_feat,
            {
                "text_conf":   conf_t.detach().cpu(),
                "audio_conf":  conf_a.detach().cpu(),
                "visual_conf": conf_v.detach().cpu(),
            }
        )


class MissingModalityHandler(nn.Module):
    def __init__(self, d_model=256,
                 text_dim=768, audio_dim=768, visual_dim=2048,
                 max_text=1, max_audio=1, max_visual=1):
        super().__init__()
        self.max_text   = max_text
        self.max_audio  = max_audio
        self.max_visual = max_visual
        self.missing_text   = nn.Parameter(torch.randn(1, max_text,   text_dim)   * 0.02)
        self.missing_audio  = nn.Parameter(torch.randn(1, max_audio,  audio_dim)  * 0.02)
        self.missing_visual = nn.Parameter(torch.randn(1, max_visual, visual_dim) * 0.02)

    def forward(self, text=None, audio=None, visual=None,
                text_mask=None, audio_mask=None, visual_mask=None,
                batch_size=1):
        device = (
            text.device if text is not None else
            audio.device if audio is not None else
            visual.device if visual is not None else
            self.missing_text.device
        )
        if text is None:
            text      = self.missing_text.expand(batch_size, -1, -1).to(device)
            text_mask = torch.zeros(batch_size, self.max_text,   dtype=torch.bool, device=device)
        if audio is None:
            audio      = self.missing_audio.expand(batch_size, -1, -1).to(device)
            audio_mask = torch.zeros(batch_size, self.max_audio,  dtype=torch.bool, device=device)
        if visual is None:
            visual      = self.missing_visual.expand(batch_size, -1, -1).to(device)
            visual_mask = torch.zeros(batch_size, self.max_visual, dtype=torch.bool, device=device)
        return text, audio, visual, text_mask, audio_mask, visual_mask


def apply_modality_dropout(t, a, v, tm, am, vm, handler,
                           dropout_prob=0.10, is_training=True):
    if not is_training or random.random() > dropout_prob:
        return t, a, v, tm, am, vm
    choice = random.randint(0, 2)
    B      = t.size(0)
    if choice == 0:
        t, _, _, tm, _, _ = handler(text=None,  audio=a, visual=v,
                                    text_mask=tm, audio_mask=am, visual_mask=vm, batch_size=B)
    elif choice == 1:
        _, a, _, _, am, _ = handler(text=t, audio=None, visual=v,
                                    text_mask=tm, audio_mask=am, visual_mask=vm, batch_size=B)
    else:
        _, _, v, _, _, vm = handler(text=t, audio=a, visual=None,
                                    text_mask=tm, audio_mask=am, visual_mask=vm, batch_size=B)
    return t, a, v, tm, am, vm


class ETTACFNFusion(nn.Module):
    def __init__(self, text_dim=768, audio_dim=768, visual_dim=2048,
                 d_model=256, num_heads=8, dropout=0.1, cfg=None):
        super().__init__()
        self.modal_dropout = cfg["training"].get("modality_dropout", 0.2) if cfg else 0.2

        self.text_proj   = ModalityProjector(text_dim,   d_model, dropout)
        self.audio_proj  = ModalityProjector(audio_dim,  d_model, dropout)
        self.visual_proj = ModalityProjector(visual_dim, d_model, dropout)

        self.missing_handler = MissingModalityHandler(
            d_model=d_model,
            text_dim=text_dim, audio_dim=audio_dim, visual_dim=visual_dim
        )
        self.intra_attn   = TrimodalIntraAttention(d_model, num_heads, dropout)
        self.hierarchical = HierarchicalFusion(d_model, num_heads, dropout)
        self.conf_gate    = TrimodalConfidenceGating(d_model)

        self.adaptive_weight_net = nn.Sequential(
            nn.Linear(d_model * 3, d_model), nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 3)
        )
        self.final_proj = nn.Sequential(
            nn.Linear(d_model, d_model), nn.LayerNorm(d_model),
            nn.GELU(), nn.Dropout(dropout)
        )

    def _mean_pool(self, x, mask=None):
        if mask is not None:
            valid = (~mask).float().unsqueeze(-1)
            return (x * valid).sum(dim=1) / valid.sum(dim=1).clamp(min=1e-9)
        return x.mean(dim=1)

    def forward(self, text, audio, visual,
                text_mask=None, audio_mask=None, visual_mask=None):
        B = (text.size(0)   if text   is not None else
             audio.size(0)  if audio  is not None else
             visual.size(0))

        if self.training:
            text, audio, visual, text_mask, audio_mask, visual_mask = apply_modality_dropout(
                text, audio, visual, text_mask, audio_mask, visual_mask,
                self.missing_handler, dropout_prob=self.modal_dropout, is_training=True
            )
        else:
            text, audio, visual, text_mask, audio_mask, visual_mask = self.missing_handler(
                text, audio, visual, text_mask, audio_mask, visual_mask, batch_size=B
            )

        T, A, V = self.text_proj(text), self.audio_proj(audio), self.visual_proj(visual)
        T, A, V = self.intra_attn(T, A, V, text_mask, audio_mask, visual_mask)

        fused_hier, speech_repr, t_pool, a_pool, attn_weights = self.hierarchical(
            T, A, V, text_mask, audio_mask, visual_mask
        )
        v_pool = self._mean_pool(V, visual_mask)

        gated_t, gated_a, gated_v, confidences = self.conf_gate(t_pool, a_pool, v_pool)
        concat  = torch.cat([gated_t, gated_a, gated_v], dim=-1)
        weights = torch.softmax(self.adaptive_weight_net(concat), dim=-1)
        weighted = (
            weights[:, 0:1] * gated_t +
            weights[:, 1:2] * gated_a +
            weights[:, 2:3] * gated_v
        )

        fused = self.final_proj(fused_hier + weighted)
        info  = {**attn_weights, **confidences, "modal_weights": weights.detach().cpu()}
        return fused, info


class EmotionClassifier(nn.Module):
    def __init__(self, d_model=256, num_classes=4, dropout=0.1):
        super().__init__()
        clf_drop = max(dropout, 0.35)
        self.net = nn.Sequential(
            nn.Linear(d_model, d_model),  nn.LayerNorm(d_model), nn.GELU(), nn.Dropout(clf_drop),
            nn.Linear(d_model, d_model // 2), nn.GELU(), nn.Dropout(clf_drop),
            nn.Linear(d_model // 2, num_classes)
        )
    def forward(self, x):
        return self.net(x)


class MultimodalEmotionModel(nn.Module):
    """Complete ET-TACFN model — cfg-based construction."""
    def __init__(self, cfg):
        super().__init__()
        m = cfg["model"]
        self.fusion = ETTACFNFusion(
            text_dim   = m["text_input_dim"],
            audio_dim  = m["audio_input_dim"],
            visual_dim = m["visual_input_dim"],
            d_model    = m["d_model"],
            num_heads  = m["num_heads"],
            dropout    = m["dropout"],
            cfg        = cfg,
        )
        self.classifier = EmotionClassifier(
            d_model     = m["d_model"],
            num_classes = m["num_classes"],
            dropout     = m["dropout"],
        )

    def forward(self, text=None, audio=None, visual=None,
                text_mask=None, audio_mask=None, visual_mask=None):
        fused, info = self.fusion(text, audio, visual, text_mask, audio_mask, visual_mask)
        logits      = self.classifier(fused)
        return logits, info


# ============================================================
#  INTEGRATION UTILITY
# ============================================================

# Default config matching the retrained checkpoint
DEFAULT_CFG = {
    "model": {
        "d_model":          256,
        "num_heads":        8,
        "dropout":          0.3,
        "num_classes":      4,
        "text_input_dim":   768,
        "audio_input_dim":  768,
        "visual_input_dim": 2048,
    },
    "training": {
        "modality_dropout": 0.2,
    }
}


def get_ettacfn_model(checkpoint_path=None, device="cpu", cfg=None):
    """
    Instantiate the retrained ET-TACFN model and optionally load weights.

    Checkpoint is expected to contain {"model_state_dict": ...}.
    Falls back to checking for a bare state dict or a "model" key for
    compatibility with older checkpoints.
    """
    if cfg is None:
        cfg = DEFAULT_CFG

    model = MultimodalEmotionModel(cfg)

    if checkpoint_path and os.path.exists(checkpoint_path):
        ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)

        # Support multiple checkpoint formats
        if isinstance(ckpt, dict):
            if "model_state_dict" in ckpt:
                state_dict = ckpt["model_state_dict"]
            elif "model" in ckpt:
                state_dict = ckpt["model"]
            else:
                state_dict = ckpt          # bare state dict
        else:
            state_dict = ckpt

        model.load_state_dict(state_dict)
        print(f"✅ Loaded ET-TACFN weights from {checkpoint_path}")
    else:
        print(f"⚠️  No checkpoint found at {checkpoint_path} — using random weights")

    model.to(device)
    model.eval()
    return model