import os
import random

import torch
import torch.nn as nn

# ============================================================
#  ET-TACFN — Enhanced Trimodal Adaptive Cross-Modal Fusion
#  Consolidated Integration File
# ============================================================

class ModalityProjector(nn.Module):
    """Projects modality features to shared d_model dimension."""
    def __init__(self, input_dim, d_model=512, dropout=0.1):
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
    """Single cross-modal attention block."""
    def __init__(self, d_model=512, num_heads=8, dropout=0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(
            embed_dim   = d_model,
            num_heads   = num_heads,
            dropout     = dropout,
            batch_first = True
        )
        self.norm1   = nn.LayerNorm(d_model)
        self.norm2   = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model),
            nn.Dropout(dropout)
        )
    def forward(self, query_mod, kv_mod, key_mask=None, need_weights=True):
        attended, attn_weights = self.attn(
            query            = query_mod,
            key              = kv_mod,
            value            = kv_mod,
            key_padding_mask = key_mask,
            need_weights     = need_weights,
            average_attn_weights = False
        )
        x = self.norm1(query_mod + self.dropout(attended))
        x = self.norm2(x + self.ffn(x))
        return x, attn_weights

class IntraModalSelfAttention(nn.Module):
    """Self-attention block for a single modality."""
    def __init__(self, d_model=512, num_heads=8, dropout=0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(
            embed_dim    = d_model,
            num_heads    = num_heads,
            dropout      = dropout,
            batch_first  = True
        )
        self.norm1   = nn.LayerNorm(d_model)
        self.norm2   = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model),
            nn.Dropout(dropout)
        )
    def forward(self, x, mask=None):
        attn_out, _ = self.self_attn(
            query            = x,
            key              = x,
            value            = x,
            key_padding_mask = mask,
            need_weights     = not self.training
        )
        x = self.norm1(x + self.dropout(attn_out))
        x = self.norm2(x + self.ffn(x))
        return x

class TrimodalIntraAttention(nn.Module):
    """Applies IntraModalSelfAttention independently to all 3 modalities."""
    def __init__(self, d_model=512, num_heads=8, dropout=0.1):
        super().__init__()
        self.text_self_attn   = IntraModalSelfAttention(d_model, num_heads, dropout)
        self.audio_self_attn  = IntraModalSelfAttention(d_model, num_heads, dropout)
        self.visual_self_attn = IntraModalSelfAttention(d_model, num_heads, dropout)
    def forward(self, text, audio, visual, text_mask=None, audio_mask=None, visual_mask=None):
        refined_text   = self.text_self_attn(text,   text_mask)
        refined_audio  = self.audio_self_attn(audio,  audio_mask)
        refined_visual = self.visual_self_attn(visual, visual_mask)
        return refined_text, refined_audio, refined_visual

class ConfidenceGate(nn.Module):
    """Produces a scalar confidence score for one modality."""
    def __init__(self, d_model=512):
        super().__init__()
        self.gate_net = nn.Sequential(
            nn.Linear(d_model, d_model // 4),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 4, 1),
            nn.Sigmoid()
        )
    def forward(self, x_pooled):
        return self.gate_net(x_pooled)

class TrimodalConfidenceGating(nn.Module):
    """Applies confidence gating to all 3 modalities."""
    def __init__(self, d_model=512):
        super().__init__()
        self.gate_text   = ConfidenceGate(d_model)
        self.gate_audio  = ConfidenceGate(d_model)
        self.gate_visual = ConfidenceGate(d_model)
    def forward(self, text_feat, audio_feat, visual_feat):
        conf_t = self.gate_text(text_feat)
        conf_a = self.gate_audio(audio_feat)
        conf_v = self.gate_visual(visual_feat)
        gated_text   = conf_t * text_feat
        gated_audio  = conf_a * audio_feat
        gated_visual = conf_v * visual_feat
        confidences = {
            "text_conf":   conf_t.detach().cpu(),
            "audio_conf":  conf_a.detach().cpu(),
            "visual_conf": conf_v.detach().cpu()
        }
        return gated_text, gated_audio, gated_visual, confidences

class MissingModalityHandler(nn.Module):
    """Provides learned fallback embeddings for absent modalities."""
    def __init__(self, d_model=512, text_dim=1024, audio_dim=768, visual_dim=256,
                 max_text=128, max_audio=300, max_visual=30):
        super().__init__()
        self.max_text   = max_text
        self.max_audio  = max_audio
        self.max_visual = max_visual
        self.missing_text   = nn.Parameter(torch.randn(1, max_text,   text_dim)   * 0.02)
        self.missing_audio  = nn.Parameter(torch.randn(1, max_audio,  audio_dim)  * 0.02)
        self.missing_visual = nn.Parameter(torch.randn(1, max_visual, visual_dim) * 0.02)
    def forward(self, text=None, audio=None, visual=None,
                text_mask=None, audio_mask=None, visual_mask=None, batch_size=1):
        device = (text.device if text is not None else
                  audio.device if audio is not None else
                  visual.device if visual is not None else
                  self.missing_text.device)
        if text is None:
            text = self.missing_text.expand(batch_size, -1, -1).to(device)
            text_mask = torch.zeros(batch_size, self.max_text, dtype=torch.bool, device=device)
        if audio is None:
            audio = self.missing_audio.expand(batch_size, -1, -1).to(device)
            audio_mask = torch.zeros(batch_size, self.max_audio, dtype=torch.bool, device=device)
        if visual is None:
            visual = self.missing_visual.expand(batch_size, -1, -1).to(device)
            visual_mask = torch.zeros(batch_size, self.max_visual, dtype=torch.bool, device=device)
        return text, audio, visual, text_mask, audio_mask, visual_mask

def apply_modality_dropout(text, audio, visual, text_mask, audio_mask, visual_mask,
                           handler, dropout_prob=0.10, is_training=True):
    if not is_training or random.random() > dropout_prob:
        return text, audio, visual, text_mask, audio_mask, visual_mask
    choice = random.randint(0, 2)
    B = text.size(0)
    if choice == 0:
        text, _, _, text_mask, _, _ = handler(None, audio, visual, text_mask, audio_mask, visual_mask, B)
    elif choice == 1:
        _, audio, _, _, audio_mask, _ = handler(text, None, visual, text_mask, audio_mask, visual_mask, B)
    else:
        _, _, visual, _, _, visual_mask = handler(text, audio, None, text_mask, audio_mask, visual_mask, B)
    return text, audio, visual, text_mask, audio_mask, visual_mask

class HierarchicalFusion(nn.Module):
    """Two-stage hierarchical cross-modal fusion."""
    def __init__(self, d_model=512, num_heads=8, dropout=0.1):
        super().__init__()
        self.cma_text_audio  = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_audio_text  = CrossModalAttention(d_model, num_heads, dropout)
        self.speech_combiner = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        self.cma_speech_visual = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_visual_speech = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_audio_visual  = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_visual_audio  = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_text_visual   = CrossModalAttention(d_model, num_heads, dropout)
        self.cma_visual_text   = CrossModalAttention(d_model, num_heads, dropout)
        self.final_combiner = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )
    def _mean_pool(self, x, mask=None):
        if mask is not None:
            valid  = (~mask).float().unsqueeze(-1)
            x      = x * valid
            pooled = x.sum(dim=1) / valid.sum(dim=1).clamp(min=1e-9)
        else:
            pooled = x.mean(dim=1)
        return pooled
    def forward(self, text, audio, visual, text_mask=None, audio_mask=None, visual_mask=None):
        ta, w_ta = self.cma_text_audio(text, audio, audio_mask)
        at, w_at = self.cma_audio_text(audio, text, text_mask)
        tv, w_tv = self.cma_text_visual(text, visual, visual_mask)
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
        fused = self.final_combiner(torch.cat([sv_pool, vs_pool], dim=-1))
        attn_weights = {
            "text_audio": w_ta, "audio_text": w_at, "text_visual": w_tv, "audio_visual": w_av,
            "speech_visual": w_sv, "visual_speech": w_vs, "visual_text": w_vt, "visual_audio": w_va,
        }
        return fused, speech, t_pool, a_pool, attn_weights

class ETTACFNFusion(nn.Module):
    """Full ET-TACFN Fusion Module."""
    def __init__(self, text_dim=1024, audio_dim=768, visual_dim=256,
                 d_model=512, num_heads=8, dropout=0.1, modal_dropout=0.15):
        super().__init__()
        self.modal_dropout = modal_dropout
        self.text_proj   = ModalityProjector(text_dim,   d_model, dropout)
        self.audio_proj  = ModalityProjector(audio_dim,  d_model, dropout)
        self.visual_proj = ModalityProjector(visual_dim, d_model, dropout)
        self.missing_handler = MissingModalityHandler(d_model, text_dim, audio_dim, visual_dim)
        self.intra_attn = TrimodalIntraAttention(d_model, num_heads, dropout)
        self.hierarchical = HierarchicalFusion(d_model, num_heads, dropout)
        self.conf_gate = TrimodalConfidenceGating(d_model)
        self.adaptive_weight_net = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 3)
        )
        self.final_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )
    def _mean_pool(self, x, mask=None):
        if mask is not None:
            valid  = (~mask).float().unsqueeze(-1)
            x      = x * valid
            pooled = x.sum(dim=1) / valid.sum(dim=1).clamp(min=1e-9)
        else:
            pooled = x.mean(dim=1)
        return pooled
    def forward(self, text, audio, visual, text_mask=None, audio_mask=None, visual_mask=None):
        B = (text.size(0) if text is not None else audio.size(0) if audio is not None else visual.size(0))
        if self.training:
            text, audio, visual, text_mask, audio_mask, visual_mask = \
                apply_modality_dropout(text, audio, visual, text_mask, audio_mask, visual_mask,
                                       self.missing_handler, dropout_prob=self.modal_dropout, is_training=True)
        else:
            text, audio, visual, text_mask, audio_mask, visual_mask = \
                self.missing_handler(text, audio, visual, text_mask, audio_mask, visual_mask, batch_size=B)
        T = self.text_proj(text)
        A = self.audio_proj(audio)
        V = self.visual_proj(visual)
        T, A, V = self.intra_attn(T, A, V, text_mask, audio_mask, visual_mask)
        fused_hier, speech_repr, t_pool, a_pool, attn_weights = self.hierarchical(T, A, V, text_mask, audio_mask, visual_mask)
        v_pool = self._mean_pool(V, visual_mask)
        gated_t, gated_a, gated_v, confidences = self.conf_gate(t_pool, a_pool, v_pool)
        concat  = torch.cat([gated_t, gated_a, gated_v], dim=-1)
        weights = torch.softmax(self.adaptive_weight_net(concat), dim=-1)
        weighted = (weights[:, 0:1] * gated_t + weights[:, 1:2] * gated_a + weights[:, 2:3] * gated_v)
        fused = self.final_proj(fused_hier + weighted)
        info = {**attn_weights, **confidences, "modal_weights": weights.detach().cpu()}
        return fused, info

class EmotionClassifier(nn.Module):
    """3-layer MLP classifier on top of fused features."""
    def __init__(self, d_model=512, num_classes=4, dropout=0.1):
        super().__init__()
        clf_drop = max(dropout, 0.35)
        self.net = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(clf_drop),
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(clf_drop),
            nn.Linear(d_model // 2, num_classes)
        )
    def forward(self, x):
        return self.net(x)

class MultimodalEmotionModel(nn.Module):
    """Complete ET-TACFN model for inference and training."""
    def __init__(self, text_dim=1024, audio_dim=768, visual_dim=256, d_model=512, num_heads=8, num_classes=4, dropout=0.1):
        super().__init__()
        self.fusion = ETTACFNFusion(text_dim, audio_dim, visual_dim, d_model, num_heads, dropout)
        self.classifier = EmotionClassifier(d_model, num_classes, dropout)
    def forward(self, text=None, audio=None, visual=None, text_mask=None, audio_mask=None, visual_mask=None):
        fused, info = self.fusion(text, audio, visual, text_mask, audio_mask, visual_mask)
        logits = self.classifier(fused)
        return logits, info

# ============================================================
#  INTERGRATION UTILITIES
# ============================================================

def get_ettacfn_model(checkpoint_path=None, device='cpu'):
    """
    Instantiates the model and optionally loads pre-trained weights.
    Audio dim is fixed to 768 to match microsoft/wavlm-base-plus training outputs.
    """
    model = MultimodalEmotionModel(
        text_dim    = 1024,
        audio_dim   = 768,    # Corrected to match WavLM-Base+
        visual_dim  = 256,
        d_model     = 512,
        num_heads   = 8,
        num_classes = 4,
        dropout     = 0.1
    )
    
    if checkpoint_path and os.path.exists(checkpoint_path):
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=False)
        # Handle cases where the checkpoint is wrapped in a 'model' key or similar
        if 'model' in state_dict:
            state_dict = state_dict['model']
        model.load_state_dict(state_dict)
        print(f"Loaded weights from {checkpoint_path}")
    
    model.to(device)
    model.eval()
    return model