import torch
import numpy as np
from pathlib import Path
import json

print("="*60)
print("FEATURE QUALITY DIAGNOSTIC")
print("="*60)

# Check vision features
print("\n1. VISION FEATURES")
vision_dir = Path(r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\vision')
vision_files = sorted(list(vision_dir.rglob('*.pt')))[:1000]
vision_samples = [torch.load(f) for f in vision_files]
vision_norms = [f.norm().item() for f in vision_samples]
vision_zeros = sum(1 for n in vision_norms if n < 0.01)

print(f"  Files checked: {len(vision_samples)}")
print(f"  Zero/near-zero: {vision_zeros} ({vision_zeros/len(vision_samples)*100:.1f}%)")
print(f"  Mean norm: {np.mean(vision_norms):.3f} ± {np.std(vision_norms):.3f}")
print(f"  Range: [{np.min(vision_norms):.3f}, {np.max(vision_norms):.3f}]")
print(f"  Median: {np.median(vision_norms):.3f}")

# Check audio features
print("\n2. AUDIO FEATURES")
audio_dir = Path(r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\audio')
audio_files = sorted(list(audio_dir.rglob('*.pt')))[:1000]
audio_samples = [torch.load(f) for f in audio_files]
audio_norms = [f.norm().item() for f in audio_samples]

print(f"  Files checked: {len(audio_samples)}")
print(f"  Mean norm: {np.mean(audio_norms):.3f} ± {np.std(audio_norms):.3f}")
print(f"  Range: [{np.min(audio_norms):.3f}, {np.max(audio_norms):.3f}]")
print(f"  Median: {np.median(audio_norms):.3f}")

# Check text features
print("\n3. TEXT FEATURES")
text_dir = Path(r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\text')
text_files = sorted(list(text_dir.rglob('*.pt')))[:1000]
text_samples = [torch.load(f) for f in text_files]
text_norms = [f.norm().item() for f in text_samples]

print(f"  Files checked: {len(text_samples)}")
print(f"  Mean norm: {np.mean(text_norms):.3f} ± {np.std(text_norms):.3f}")
print(f"  Range: [{np.min(text_norms):.3f}, {np.max(text_norms):.3f}]")
print(f"  Median: {np.median(text_norms):.3f}")

# Scale analysis
print("\n" + "="*60)
print("SCALE MISMATCH ANALYSIS")
print("="*60)

vision_mean = np.mean(vision_norms)
audio_mean = np.mean(audio_norms)
text_mean = np.mean(text_norms)

print(f"\nRelative scales (normalized to audio):")
print(f"  Vision/Audio ratio: {vision_mean/audio_mean:.2f}x")
print(f"  Text/Audio ratio: {text_mean/audio_mean:.2f}x")
print(f"  Vision/Text ratio: {vision_mean/text_mean:.2f}x")

if vision_mean / audio_mean > 2.0 or vision_mean / audio_mean < 0.5:
    print(f"\n⚠️  WARNING: SIGNIFICANT SCALE MISMATCH DETECTED!")
    print(f"  Vision features are {vision_mean/audio_mean:.1f}x different from audio")
    print(f"  Recommendation: Apply feature normalization")

# Check for missing vision features in index
print("\n" + "="*60)
print("INDEX VALIDATION")
print("="*60)

train_index = json.load(open(r'd:\Multimodal-Empathetical-Conversational-Companion\training\train_index.json'))
test_index = json.load(open(r'd:\Multimodal-Empathetical-Conversational-Companion\training\test_index.json'))

train_missing_vision = sum(1 for item in train_index if item['vision'] is None)
test_missing_vision = sum(1 for item in test_index if item['vision'] is None)

print(f"\nTrain set:")
print(f"  Total samples: {len(train_index)}")
print(f"  Missing vision: {train_missing_vision} ({train_missing_vision/len(train_index)*100:.1f}%)")

print(f"\nTest set:")
print(f"  Total samples: {len(test_index)}")
print(f"  Missing vision: {test_missing_vision} ({test_missing_vision/len(test_index)*100:.1f}%)")

if train_missing_vision > 0 or test_missing_vision > 0:
    print(f"\n⚠️  WARNING: Some samples have missing vision features!")
    print(f"  These will be filled with zeros, potentially degrading performance")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

issues = []
if vision_zeros / len(vision_samples) > 0.05:
    issues.append(f"High zero rate in vision ({vision_zeros/len(vision_samples)*100:.1f}%)")

if vision_mean / audio_mean > 2.0 or vision_mean / audio_mean < 0.5:
    issues.append(f"Scale mismatch: vision norm is {vision_mean/audio_mean:.1f}x audio")

if train_missing_vision > 100:
    issues.append(f"Many missing vision features ({train_missing_vision})")

if issues:
    print("\nIssues found:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\nSuggested fixes:")
    print("  1. Add feature normalization (L2 normalize each modality)")
    print("  2. Reduce dropout to 0.1 (less aggressive regularization)")
    print("  3. Use separate learning rates for different modality branches")
    print("  4. Add batch normalization after fusion")
else:
    print("\n✓ No obvious feature quality issues detected")
    print("  Problem likely in model architecture or training strategy")
