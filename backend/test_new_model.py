"""
Quick smoke-test for the retrained ET-TACFN model.
Run from the backend/ directory:
    python test_new_model.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import torch

print("=" * 60)
print("ET-TACFN Retrained Model — Smoke Test")
print("=" * 60)

# ── 1. Load model ────────────────────────────────────────────
print("\n[1] Loading model from checkpoints/best_model.pt ...")
from models.emotion_classifier import get_ettacfn_model

model = get_ettacfn_model(
    checkpoint_path="checkpoints/best_model.pt",
    device="cpu"
)
print(f"    Model loaded ✅  (device: cpu)")
param_count = sum(p.numel() for p in model.parameters())
print(f"    Parameters: {param_count:,}")

# ── 2. Run inference with dummy features ─────────────────────
print("\n[2] Running inference with dummy features ...")

# Simulate: audio [1, 50, 768], text [1, 128, 768], visual=None
audio  = torch.randn(1, 50,  768)   # WavLM-base sequence output
text   = torch.randn(1, 128, 768)   # RoBERTa-base sequence output
visual = None                        # MissingModalityHandler handles this

with torch.no_grad():
    logits, info = model(text=text, audio=audio, visual=visual)

probs = torch.softmax(logits, dim=-1).squeeze(0)
emotion_map = {0: "happy", 1: "sad", 2: "angry", 3: "neutral"}
pred_idx    = int(probs.argmax())

print(f"    Output shape: {logits.shape}  (expected: [1, 4])")
assert logits.shape == (1, 4), f"Shape mismatch: {logits.shape}"

print(f"\n    Probabilities:")
for i, p in enumerate(probs.tolist()):
    marker = " ←" if i == pred_idx else ""
    print(f"      {emotion_map[i]:8s}: {p:.4f}{marker}")

print(f"\n    Predicted emotion: {emotion_map[pred_idx].upper()} ({probs[pred_idx]:.2%})")

# ── 3. Verify modal_weights are returned ─────────────────────
print("\n[3] Checking attention info dict ...")
assert "modal_weights" in info, "modal_weights missing from info!"
weights = info["modal_weights"].squeeze(0).tolist()
print(f"    Modal weights → text: {weights[0]:.3f}  audio: {weights[1]:.3f}  visual: {weights[2]:.3f}")

# ── 4. Test with explicit visual (2048-dim) ───────────────────
print("\n[4] Testing with explicit visual features [1, 10, 2048] ...")
visual_feats = torch.randn(1, 10, 2048)
with torch.no_grad():
    logits2, info2 = model(text=text, audio=audio, visual=visual_feats)
assert logits2.shape == (1, 4)
weights2 = info2["modal_weights"].squeeze(0).tolist()
print(f"    Modal weights → text: {weights2[0]:.3f}  audio: {weights2[1]:.3f}  visual: {weights2[2]:.3f}")
print(f"    Predicted: {emotion_map[int(logits2.argmax(dim=-1))]}")

print("\n" + "=" * 60)
print("✅ All checks passed — model is ready for deployment!")
print("=" * 60)
