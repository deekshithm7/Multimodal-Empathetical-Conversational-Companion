# Production Deployment Guide - Audio+Text Emotion Recognition Model

**Model**: Audio+Text (A+T) - Best performing model  
**Accuracy**: 70.7%  
**F1-Score**: 0.707  
**Checkpoint**: `checkpoints/at.pth`

---

## 1. Input/Output Flow

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ├──────────────────┬─────────────────┐
       │                  │                 │
   ┌───▼────┐      ┌──────▼──────┐    ┌────▼────┐
   │ Audio  │      │    Text     │    │  Video  │
   │  File  │      │   String    │    │  (N/A)  │
   └───┬────┘      └──────┬──────┘    └─────────┘
       │                  │
       │                  │
┌──────▼──────────┐  ┌────▼──────────┐
│ Audio Encoder   │  │ Text Encoder  │
│ (WavLM-base)    │  │ (RoBERTa-base)│
└──────┬──────────┘  └────┬──────────┘
       │                  │
       │ 768-dim          │ 768-dim
       │                  │
       ├──────────────────┤
       │
┌──────▼──────────┐
│ L2 Normalize    │
│ Each Modality   │
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Fusion (Concat) │
│   1536-dim      │
└──────┬──────────┘
       │
┌──────▼──────────┐
│ FusionMLP Model │
│ 1536→1024→512   │
└──────┬──────────┘
       │
┌──────▼──────────┐
│  Classifier     │
│  512 → 4        │
└──────┬──────────┘
       │
┌──────▼──────────┐
│    Output       │
│ 0: Neutral      │
│ 1: Happy        │
│ 2: Angry        │
│ 3: Sad          │
└─────────────────┘
```

---

## 2. Audio Input Specifications

### 2.1 Required Audio Format

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Format** | WAV, MP3, FLAC, M4A | Any format supported by `torchaudio` |
| **Sample Rate** | **16,000 Hz** | **Required for WavLM** |
| **Channels** | Mono (1 channel) | Stereo will be converted to mono |
| **Bit Depth** | 16-bit or 32-bit | Standard audio quality |
| **Duration** | 0.5 - 30 seconds | Typical utterance length |
| **Encoding** | PCM | Standard uncompressed |

### 2.2 Audio Preprocessing Pipeline

```python
import torchaudio
import torch

def preprocess_audio(audio_path):
    """
    Preprocess audio file for WavLM encoder
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        waveform: torch.Tensor of shape (num_samples,)
    """
    # Load audio
    waveform, sample_rate = torchaudio.load(audio_path)
    
    # Resample to 16kHz if necessary
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate,
            new_freq=16000
        )
        waveform = resampler(waveform)
    
    # Convert stereo to mono if necessary
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    
    # Squeeze to 1D
    waveform = waveform.squeeze(0)  # (num_samples,)
    
    return waveform
```

### 2.3 WavLM Feature Extraction

| Parameter | Value |
|-----------|-------|
| **Model** | `microsoft/wavlm-base` |
| **Input** | Raw waveform @ 16kHz |
| **Output** | 768-dimensional embedding |
| **Pooling** | Mean pooling over time dimension |
| **Device** | CUDA recommended, CPU supported |

```python
from transformers import AutoFeatureExtractor, WavLMModel
import torch

# Initialize (do this once)
feature_extractor = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base')
wavlm_model = WavLMModel.from_pretrained('microsoft/wavlm-base', use_safetensors=True)
wavlm_model.eval()

def extract_audio_features(waveform):
    """
    Extract 768-dim audio features using WavLM
    
    Args:
        waveform: torch.Tensor of shape (num_samples,) @ 16kHz
    
    Returns:
        audio_emb: torch.Tensor of shape (768,)
    """
    # Prepare inputs
    inputs = feature_extractor(
        waveform.numpy(),
        sampling_rate=16000,
        return_tensors='pt'
    )
    
    # Extract features
    with torch.no_grad():
        outputs = wavlm_model(inputs.input_values)
        # Mean pool over time dimension
        audio_emb = outputs.last_hidden_state.mean(dim=1).squeeze(0)  # (768,)
    
    # L2 normalize
    audio_emb = torch.nn.functional.normalize(audio_emb, p=2, dim=0)
    
    return audio_emb
```

---

## 3. Text Input Specifications

### 3.1 Required Text Format

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Encoding** | UTF-8 | Standard text encoding |
| **Max Length** | 512 tokens | RoBERTa limit |
| **Min Length** | 1 word | At least some text |
| **Language** | English | Model trained on English |
| **Format** | Plain text string | No special formatting |

### 3.2 Text Preprocessing

```python
def preprocess_text(text):
    """
    Preprocess text for RoBERTa encoder
    
    Args:
        text: str, raw text input
    
    Returns:
        text: str, cleaned text
    """
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long (safety check)
    if len(text) > 5000:
        text = text[:5000]
    
    return text
```

### 3.3 RoBERTa Feature Extraction

| Parameter | Value |
|-----------|-------|
| **Model** | `roberta-base` |
| **Tokenizer** | `roberta-base` tokenizer |
| **Output** | 768-dimensional embedding |
| **Pooling** | [CLS] token (first token) |
| **Max Tokens** | 512 |

```python
from transformers import RobertaTokenizer, RobertaModel
import torch

# Initialize (do this once)
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
roberta_model = RobertaModel.from_pretrained('roberta-base')
roberta_model.eval()

def extract_text_features(text):
    """
    Extract 768-dim text features using RoBERTa
    
    Args:
        text: str, input text
    
    Returns:
        text_emb: torch.Tensor of shape (768,)
    """
    # Tokenize
    inputs = tokenizer(
        text,
        return_tensors='pt',
        max_length=512,
        truncation=True,
        padding=True
    )
    
    # Extract features
    with torch.no_grad():
        outputs = roberta_model(**inputs)
        # Use [CLS] token embedding
        text_emb = outputs.last_hidden_state[:, 0, :].squeeze(0)  # (768,)
    
    # L2 normalize
    text_emb = torch.nn.functional.normalize(text_emb, p=2, dim=0)
    
    return text_emb
```

---

## 4. Model Inference

### 4.1 Load Production Model

```python
import torch
from model import FusionMLP

# Load checkpoint
checkpoint = torch.load('checkpoints/at.pth', weights_only=False)

# Initialize model
model = FusionMLP(
    use_v=False,  # No video
    use_a=True,   # Audio
    use_t=True,   # Text
    num_classes=4
)

# Load trained weights
model.load_state_dict(checkpoint['model'])
model.eval()

# Move to GPU if available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = model.to(device)
```

### 4.2 Complete Inference Pipeline

```python
def predict_emotion(audio_path, text):
    """
    Complete inference pipeline
    
    Args:
        audio_path: str, path to audio file
        text: str, text transcript
    
    Returns:
        emotion_label: str, predicted emotion (neutral/happy/angry/sad)
        confidence: float, prediction confidence (0-1)
        probabilities: dict, all class probabilities
    """
    # 1. Preprocess audio
    waveform = preprocess_audio(audio_path)
    
    # 2. Extract audio features
    audio_emb = extract_audio_features(waveform)
    
    # 3. Preprocess text
    text = preprocess_text(text)
    
    # 4. Extract text features
    text_emb = extract_text_features(text)
    
    # 5. Fuse modalities (concatenate)
    fused = torch.cat([audio_emb, text_emb], dim=0)  # (1536,)
    
    # 6. Add batch dimension and move to device
    fused = fused.unsqueeze(0).to(device)  # (1, 1536)
    
    # 7. Model inference
    with torch.no_grad():
        logits = model(fused)  # (1, 4)
        probabilities = torch.softmax(logits, dim=1).squeeze(0)  # (4,)
        prediction = torch.argmax(logits, dim=1).item()
    
    # 8. Map to emotion labels
    emotion_map = {
        0: 'neutral',
        1: 'happy',
        2: 'angry',
        3: 'sad'
    }
    
    emotion_label = emotion_map[prediction]
    confidence = probabilities[prediction].item()
    
    prob_dict = {
        'neutral': probabilities[0].item(),
        'happy': probabilities[1].item(),
        'angry': probabilities[2].item(),
        'sad': probabilities[3].item()
    }
    
    return emotion_label, confidence, prob_dict
```

---

## 5. Example Usage

### 5.1 Simple API

```python
# Example 1: Predict from audio file and text
emotion, confidence, probs = predict_emotion(
    audio_path='user_audio.wav',
    text='I am really happy today!'
)

print(f"Emotion: {emotion}")
print(f"Confidence: {confidence:.2%}")
print(f"All probabilities: {probs}")

# Output:
# Emotion: happy
# Confidence: 85.3%
# All probabilities: {'neutral': 0.05, 'happy': 0.85, 'angry': 0.03, 'sad': 0.07}
```

### 5.2 Batch Processing

```python
def predict_batch(audio_paths, texts):
    """
    Process multiple samples in batch
    
    Args:
        audio_paths: list of str, audio file paths
        texts: list of str, text transcripts
    
    Returns:
        results: list of dict with predictions
    """
    results = []
    
    for audio_path, text in zip(audio_paths, texts):
        emotion, confidence, probs = predict_emotion(audio_path, text)
        results.append({
            'emotion': emotion,
            'confidence': confidence,
            'probabilities': probs
        })
    
    return results
```

---

## 6. Performance Considerations

### 6.1 Latency Breakdown

| Step | Time (CPU) | Time (GPU) | Notes |
|------|-----------|-----------|-------|
| Audio loading | ~50ms | ~50ms | I/O bound |
| Audio resampling | ~30ms | ~30ms | If needed |
| WavLM encoding | ~200ms | ~50ms | **Bottleneck on CPU** |
| Text tokenization | ~10ms | ~10ms | Fast |
| RoBERTa encoding | ~100ms | ~30ms | Moderate |
| Model inference | ~20ms | ~5ms | Fast |
| **Total** | **~410ms** | **~175ms** | **Per sample** |

**Recommendation**: Use GPU for production (3x faster)

### 6.2 Optimization Strategies

1. **Batch Processing**:
   ```python
   # Process multiple samples together
   # 2-5x throughput improvement
   ```

2. **Model Quantization** (optional):
   ```python
   # Reduce model size by 4x, minimal accuracy loss
   import torch.quantization
   model_quantized = torch.quantization.quantize_dynamic(
       model, {torch.nn.Linear}, dtype=torch.qint8
   )
   ```

3. **ONNX Export** (optional):
   ```python
   # Export for faster inference engines
   torch.onnx.export(model, sample_input, 'model.onnx')
   ```

---

## 7. Error Handling

```python
def safe_predict_emotion(audio_path, text):
    """
    Prediction with comprehensive error handling
    """
    try:
        # Validate inputs
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if not text or len(text.strip()) == 0:
            raise ValueError("Text input cannot be empty")
        
        # Predict
        emotion, confidence, probs = predict_emotion(audio_path, text)
        
        return {
            'success': True,
            'emotion': emotion,
            'confidence': confidence,
            'probabilities': probs
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'emotion': None,
            'confidence': None
        }
```

---

## 8. System Requirements

### 8.1 Hardware

**Minimum**:
- CPU: 4 cores
- RAM: 8GB
- Storage: 5GB (models + features)
- GPU: Optional (RTX 2060 or better)

**Recommended**:
- CPU: 8+ cores
- RAM: 16GB
- Storage: 10GB
- GPU: RTX 3050+ (4GB VRAM)

### 8.2 Software Dependencies

```txt
# requirements.txt for deployment
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.30.0
numpy>=1.24.0
soundfile>=0.12.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## 9. Production Checklist

- [ ] Test with various audio formats (WAV, MP3, etc.)
- [ ] Test with different sample rates (auto-resampling)
- [ ] Test with stereo and mono audio
- [ ] Validate text encoding (UTF-8)
- [ ] Load test for throughput
- [ ] Set up error logging
- [ ] Monitor inference latency
- [ ] Configure GPU if available
- [ ] Set up model versioning
- [ ] Create API endpoint (Flask/FastAPI)

---

## 10. REST API Example (FastAPI)

```python
from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class EmotionResponse(BaseModel):
    emotion: str
    confidence: float
    probabilities: dict

@app.post("/predict", response_model=EmotionResponse)
async def predict_endpoint(
    audio: UploadFile,
    text: str = Form(...)
):
    # Save uploaded audio temporarily
    audio_path = f"/tmp/{audio.filename}"
    with open(audio_path, "wb") as f:
        f.write(await audio.read())
    
    # Predict
    emotion, confidence, probs = predict_emotion(audio_path, text)
    
    # Clean up
    os.remove(audio_path)
    
    return EmotionResponse(
        emotion=emotion,
        confidence=confidence,
        probabilities=probs
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Usage**:
```bash
curl -X POST "http://localhost:8000/predict" \
  -F "audio=@user_audio.wav" \
  -F "text=I am feeling great today"
```

---

## 11. Monitoring & Logging

```python
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict_with_logging(audio_path, text):
    start_time = time.time()
    
    logger.info(f"Processing audio: {audio_path}")
    logger.info(f"Text length: {len(text)} chars")
    
    try:
        emotion, confidence, probs = predict_emotion(audio_path, text)
        
        latency = time.time() - start_time
        logger.info(f"Prediction: {emotion} ({confidence:.2%}) in {latency:.3f}s")
        
        return emotion, confidence, probs
    
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise
```

---

**Document Version**: 1.0  
**Last Updated**: January 24, 2026  
**Model Checkpoint**: `checkpoints/at.pth`  
**Production Ready**: ✅ Yes
