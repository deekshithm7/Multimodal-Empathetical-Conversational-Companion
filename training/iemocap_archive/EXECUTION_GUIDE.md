# IEMOCAP Training Execution Guide

## Quick Start (Complete Pipeline)

### Step 1: Install Additional Dependencies
```bash
cd d:\Multimodal-Empathetical-Conversational-Companion\training\src
.\venv311\Scripts\pip.exe install opencv-python tqdm
```

### Step 2: Extract Text Features (~30 min)
```bash
.\venv311\Scripts\python.exe cache_text.py
```
**Output**: `../features/text/Session*/` with ~10k utterance `.pt` files

### Step 3: Extract Audio Features (~1-2 hours)
```bash
.\venv311\Scripts\python.exe cache_audio.py
```
**Output**: `../features/audio/Session*/` with ~10k utterance `.pt` files

### Step 4: Extract Video Features (~2-3 hours) [OPTIONAL]
```bash
.\venv311\Scripts\python.exe cache_video.py
```
**Note**: Video extraction is slow and optional. You can skip and use Audio+Text only.

### Step 5: Build Dataset Index
```bash
.\venv311\Scripts\python.exe build_index.py
```
**Output**: 
- `../train_index.json` (Sessions 1-4)
- `../test_index.json` (Session 5)

### Step 6: Run Single Training Test
```bash
.\venv311\Scripts\python.exe train.py --config ../configs/at.json
```
Use `at.json` (Audio+Text) to avoid video dependency initially.

### Step 7: Run All Ablations
```bash
.\venv311\Scripts\python.exe run_ablations.py
```
**Output**: Trains all 7 modality combinations and saves checkpoints

---

## Troubleshooting

### If CUDA runs out of memory (4GB VRAM):
1. Reduce batch size in configs (change from 16 to 8 or 4)
2. Process features one session at a time
3. Skip video features initially

### If video extraction fails:
- Videos in IEMOCAP are at dialog-level, not utterance-level
- Safe to skip and train with Audio+Text only (still multimodal!)
- Edit configs to set `"use_v": false`

---

## Expected Training Time (RTX 3050)

| Phase | Time Estimate |
|-------|---------------|
| Text caching | 30 min |
| Audio caching | 1-2 hours |
| Video caching | 2-3 hours (OPTIONAL) |
| Index building | < 1 min |
| Single training (2 epochs) | 5-10 min |
| All 7 ablations | 30-60 min |

---

## Next: Start Feature Extraction!

Run these commands in order:
```bash
cd d:\Multimodal-Empathetical-Conversational-Companion\training\src
.\venv311\Scripts\python.exe cache_text.py
```
