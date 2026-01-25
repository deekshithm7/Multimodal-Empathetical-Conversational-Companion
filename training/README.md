# RAVDESS Training Directory

Clean training directory for RAVDESS multimodal emotion recognition.

## Directory Structure

```
training/
├── src/                              # Source code
│   ├── ravdess_cache_text.py        # Extract text features from MP4
│   ├── ravdess_cache_audio.py       # Extract audio from MP4 (requires ffmpeg)
│   ├── ravdess_cache_video.py       # Extract video features from MP4
│   ├── ravdess_build_index.py       # Build train/test split
│   ├── ravdess_dataset.py           # Dataset loader
│   ├── ravdess_test.py              # Quick validation test
│   ├── ravdess_comprehensive_train.py  # Automated training pipeline ⭐
│   ├── train.py                     # Main training script
│   ├── model.py                     # Model architecture
│   ├── fusion.py                    # Feature fusion
│   ├── eval.py                      # Metrics computation
│   └── requirements.txt             # Python dependencies
│
├── configs/                          # Configuration files
│   ├── ravdess_at_test.json         # Audio+Text test config
│   └── ravdess_vat_test.json        # Vision+Audio+Text test config
│
├── features/ravdess/                 # Cached features (after extraction)
│   ├── text/                        # RoBERTa embeddings (768-dim)
│   ├── audio/                       # WavLM embeddings (768-dim)
│   └── vision/                      # ResNet50 embeddings (2048-dim)
│
├── checkpoints/                      # Saved model checkpoints
│
├── ravdess_train_index.json         # Training data index
├── ravdess_test_index.json          # Testing data index
│
└── iemocap_archive/                 # IEMOCAP files (archived for reference)

```

## Quick Start

### 1. Feature Extraction (one-time, ~2-3 hours for 24 actors)

```powershell
cd src
python ravdess_cache_text.py
python ravdess_cache_audio.py   # Requires ffmpeg
python ravdess_cache_video.py
python ravdess_build_index.py
```

### 2. Quick Test

```powershell
python ravdess_test.py  # Tests A+T and V+A+T models
```

### 3. Comprehensive Training

```powershell
# Random 20 experiments (~2-4 hours)
python ravdess_comprehensive_train.py --num_experiments 20

# Results saved to: ../RAVDESS_TRAINING_RESULTS.md
```

## Dataset Info

- **Current**: 9 actors (1-9) = 1080 samples
- **Full Dataset**: 24 actors = 2880 samples
- **Classes**: 4 (Neutral, Happy, Sad, Angry)
- **Split**: Odd actors = Train, Even actors = Test

## Expected Performance

| Modality | Expected Accuracy |
|----------|-------------------|
| Text (T) | ~45-50% |
| Audio (A) | ~55-60% |
| **Audio+Text (A+T)** | **~70-75%** ⭐ |
| V+A+T | ~65-70% |

## Requirements

- Python 3.8+
- PyTorch
- transformers
- opencv-python
- pydub
- **ffmpeg** (for audio extraction)

See `../brain/.../ffmpeg_installation.md` for ffmpeg setup.
