# IEMOCAP Archive

This folder contains all IEMOCAP-related files that were used in the previous training experiments.

## Contents

### src/
- `build_index.py` - IEMOCAP index builder
- `cache_audio.py` - IEMOCAP audio feature extraction
- `cache_text.py` - IEMOCAP text feature extraction  
- `cache_video_utterances.py` - IEMOCAP video feature extraction
- `iemocap_dataset.py` - IEMOCAP dataset loader
- `run_ablations.py` - IEMOCAP ablation study runner

### configs/
- `at.json` - Audio+Text config
- `vat.json` - Vision+Audio+Text config
- `audio_only.json`, `text_only.json`, `vision_only.json` - Single modality configs
- `va.json`, `vt.json` - Dual modality configs

### Root
- `train_index.json` - IEMOCAP training index (4,290 samples)
- `test_index.json` - IEMOCAP testing index (1,241 samples)
- `TRAINING_RESULTS.md` - Complete IEMOCAP training results (70.7% accuracy achieved)
- `DEPLOYMENT_GUIDE.md` - IEMOCAP deployment documentation
- `EXECUTION_GUIDE.md` - IEMOCAP execution instructions
- `IMPROVEMENT_STRATEGIES.md` - Ideas for improving IEMOCAP models

## IEMOCAP Training Results Summary

**Best Model**: Audio+Text (A+T)
- Accuracy: 70.7%
- F1-Score: 0.707
- Configuration: Dropout=0.3, Weight Decay=0.01, Early Stopping

These files are kept for reference but the current training pipeline focuses on RAVDESS dataset.
