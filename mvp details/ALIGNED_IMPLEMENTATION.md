# MECC Implementation - Aligned with Existing MVP

## Video Processing Strategy

### Current Approach: Send Video to Backend

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                     │
│  - Records video with MediaRecorder API                │
│  - Sends video blob to backend                         │
│  - No local ML processing                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ POST video blob
                 │
┌────────────────▼────────────────────────────────────────┐
│                    BACKEND (FastAPI)                    │
│                                                         │
│  1. Receive video file                                 │
│  2. Extract audio track (ffmpeg/librosa)              │
│  3. Process audio:                                     │
│     - Audio → WavLM → 768-dim                        │
│     - Audio → Whisper → Text → RoBERTa → 768-dim    │
│  4. Concatenate → 1536-dim                            │
│  5. Predict emotion (your trained model)              │
│  6. Generate response (Claude LLM)                     │
│  7. Convert to speech (OpenAI TTS)                    │
│  8. Return response + audio                            │
└─────────────────────────────────────────────────────────┘
```

**Why this approach:**
- ✅ Frontend stays simple (just record & send)
- ✅ All ML models on backend (GPU acceleration)
- ✅ Consistent processing environment
- ✅ Easy to add video processing later
- ✅ Matches your existing MVP structure

---

## Existing MVP Tech Stack Alignment

### Frontend Dependencies (Already in Your MVP)

```json
{
  "dependencies": {
    "react": "^19.2.0",
    "typescript": "^5.9.0",
    "vite": "^7.2.0",
    "three": "^0.182.0",
    "@react-three/fiber": "latest",
    "@react-three/drei": "latest",
    "tailwindcss": "^4.1.0",
    "framer-motion": "^12.26.0",
    "lucide-react": "latest",
    "zustand": "^5.0.0"
  }
}
```

**No changes needed to frontend dependencies!** ✅

### Backend Dependencies (Aligned with Your Stack)

```txt
# Core ML (Already in your MVP)
torch>=2.0.0
transformers>=4.30.0

# Audio (Already in your MVP)
librosa>=0.10.0
soundfile>=0.12.0
openai-whisper>=20230314  # Using 'small' model as in your MVP

# Vision (Already in your MVP - for future)
opencv-python>=4.8.0
torchvision>=0.15.0

# API (Already in your MVP)
fastapi>=0.100.0
uvicorn>=0.23.0

# New additions for complete flow:
anthropic>=0.25.0  # For LLM responses
openai>=1.0.0      # For TTS
sqlalchemy>=2.0.0  # For database
psycopg2-binary>=2.9.0
```

---

## Updated Video Processing Service

```python
# services/video_processor.py
"""
Video processing service - extracts audio from video
Currently: Audio + Text only (skip video frames for MVP)
"""

import os
import tempfile
import subprocess
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Process video files to extract audio.
    For MVP: We only use audio track, skip video frames.
    """
    
    @staticmethod
    def extract_audio_from_video(video_path: str) -> str:
        """
        Extract audio track from video file using ffmpeg.
        
        Args:
            video_path: Path to video file (MP4, WebM, etc.)
        
        Returns:
            Path to extracted audio file (WAV, 16kHz, mono)
        """
        # Create temp file for audio
        audio_fd, audio_path = tempfile.mkstemp(suffix='.wav')
        os.close(audio_fd)
        
        try:
            # Use ffmpeg to extract audio
            # -i: input file
            # -vn: no video (audio only)
            # -ar 16000: resample to 16kHz (required by WavLM/Whisper)
            # -ac 1: convert to mono
            # -acodec pcm_s16le: WAV format
            
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-acodec', 'pcm_s16le',  # WAV codec
                '-y',  # Overwrite output
                audio_path
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr}")
            
            logger.info(f"Extracted audio from video: {audio_path}")
            return audio_path
        
        except FileNotFoundError:
            # ffmpeg not installed, try librosa as fallback
            logger.warning("ffmpeg not found, using librosa (slower)")
            return VideoProcessor._extract_audio_librosa(video_path)
        
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            # Cleanup
            if os.path.exists(audio_path):
                os.unlink(audio_path)
            raise
    
    @staticmethod
    def _extract_audio_librosa(video_path: str) -> str:
        """
        Fallback: Extract audio using librosa (slower but no ffmpeg required)
        """
        import librosa
        import soundfile as sf
        
        # Load video and extract audio
        # librosa can read video files directly (uses audioread)
        try:
            waveform, sr = librosa.load(video_path, sr=16000, mono=True)
            
            # Save to WAV
            audio_fd, audio_path = tempfile.mkstemp(suffix='.wav')
            os.close(audio_fd)
            
            sf.write(audio_path, waveform, 16000)
            
            logger.info(f"Extracted audio using librosa: {audio_path}")
            return audio_path
        
        except Exception as e:
            raise Exception(f"Could not extract audio from video: {e}")
    
    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """
        Get video duration in seconds.
        """
        import librosa
        
        try:
            # Quick method: use librosa to get duration
            duration = librosa.get_duration(path=video_path)
            return duration
        except:
            # Fallback: load and calculate
            waveform, sr = librosa.load(video_path, sr=None)
            return len(waveform) / sr
    
    @staticmethod
    def validate_video_file(video_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate video file format and duration.
        
        Returns:
            (is_valid, error_message)
        """
        # Check file exists
        if not os.path.exists(video_path):
            return False, "File not found"
        
        # Check file size (max 100MB for MVP)
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb > 100:
            return False, f"File too large: {file_size_mb:.1f}MB (max 100MB)"
        
        # Check duration
        try:
            duration = VideoProcessor.get_video_duration(video_path)
            
            if duration < 1:
                return False, "Video too short (min 1 second)"
            
            if duration > 60:
                return False, f"Video too long: {duration:.1f}s (max 60s)"
            
            return True, None
        
        except Exception as e:
            return False, f"Invalid video file: {str(e)}"


# Singleton instance
_video_processor = VideoProcessor()

def get_video_processor() -> VideoProcessor:
    """Get global video processor instance"""
    return _video_processor
```

---

## Updated Emotion Service (Handles Video Input)

```python
# services/emotion_service.py (UPDATE)
"""
Emotion Recognition Service - Updated to handle video input
Extracts audio from video, then processes Audio + Text
"""

import torch
import torch.nn.functional as F
from transformers import AutoFeatureExtractor, AutoModel, AutoTokenizer
import numpy as np
from typing import Optional, Dict
import logging
import os

logger = logging.getLogger(__name__)


class EmotionRecognitionService:
    """
    Emotion recognition from Audio + Text.
    Now accepts video files (extracts audio automatically).
    """
    
    def __init__(self, checkpoint_path: str = 'checkpoints/at.pth', device: str = 'cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        logger.info(f"Initializing EmotionRecognitionService on {self.device}")
        
        # Load audio encoder (WavLM-base) - MATCHES YOUR MVP
        logger.info("Loading WavLM audio encoder...")
        self.audio_processor = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base')
        self.audio_model = AutoModel.from_pretrained('microsoft/wavlm-base').to(self.device)
        self.audio_model.eval()
        
        # Load text encoder (RoBERTa-base) - MATCHES YOUR MVP
        logger.info("Loading RoBERTa text encoder...")
        self.text_tokenizer = AutoTokenizer.from_pretrained('roberta-base')
        self.text_model = AutoModel.from_pretrained('roberta-base').to(self.device)
        self.text_model.eval()
        
        # Load trained emotion classifier
        logger.info(f"Loading emotion classifier from {checkpoint_path}...")
        from models.fusion_mlp import FusionMLP
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.classifier = FusionMLP(use_v=False, use_a=True, use_t=True, num_classes=4)
        self.classifier.load_state_dict(checkpoint['model'])
        self.classifier.to(self.device)
        self.classifier.eval()
        
        # Emotion mapping
        self.emotion_map = {0: 'neutral', 1: 'happy', 2: 'angry', 3: 'sad'}
        
        logger.info("✅ EmotionRecognitionService initialized successfully")
    
    def extract_audio_features(self, audio_path: str) -> np.ndarray:
        """Extract 768-dim audio features using WavLM"""
        import librosa
        
        try:
            # Load audio at 16kHz (WavLM requirement)
            waveform, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Process with WavLM
            inputs = self.audio_processor(waveform, sampling_rate=16000, return_tensors='pt')
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.audio_model(**inputs)
                # Mean pooling over time
                audio_emb = outputs.last_hidden_state.mean(dim=1).squeeze()  # [768]
            
            # L2 normalize (CRITICAL - matches training)
            audio_emb = F.normalize(audio_emb, p=2, dim=0)
            
            return audio_emb.cpu().numpy()
        
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            raise
    
    def extract_text_features(self, text: str) -> np.ndarray:
        """Extract 768-dim text features using RoBERTa"""
        try:
            # Tokenize
            inputs = self.text_tokenizer(
                text,
                return_tensors='pt',
                max_length=128,
                truncation=True,
                padding='max_length'
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.text_model(**inputs)
                # Mean pooling over sequence
                text_emb = outputs.last_hidden_state.mean(dim=1).squeeze()  # [768]
            
            # L2 normalize (CRITICAL - matches training)
            text_emb = F.normalize(text_emb, p=2, dim=0)
            
            return text_emb.cpu().numpy()
        
        except Exception as e:
            logger.error(f"Error extracting text features: {e}")
            raise
    
    def predict_emotion(
        self,
        video_path: Optional[str] = None,  # NEW: Accept video files
        audio_path: Optional[str] = None,
        text: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Predict emotion from video, audio, and/or text.
        
        Args:
            video_path: Path to video file (will extract audio)
            audio_path: Path to audio file (if no video)
            text: Text string (if available)
        
        Returns:
            Emotion prediction dictionary
        """
        if not video_path and not audio_path and not text:
            raise ValueError("Must provide video, audio, or text")
        
        temp_audio = None
        
        try:
            # Handle video input: extract audio
            if video_path:
                from services.video_processor import get_video_processor
                processor = get_video_processor()
                
                # Extract audio from video
                temp_audio = processor.extract_audio_from_video(video_path)
                audio_path = temp_audio
                
                logger.info(f"Extracted audio from video: {audio_path}")
            
            # Extract features
            if audio_path:
                audio_features = self.extract_audio_features(audio_path)
            else:
                audio_features = np.zeros(768, dtype=np.float32)
            
            if text:
                text_features = self.extract_text_features(text)
            else:
                text_features = np.zeros(768, dtype=np.float32)
            
            # Concatenate [1536-dim]
            fused_features = np.concatenate([audio_features, text_features])
            fused_tensor = torch.from_numpy(fused_features).float().unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                logits = self.classifier(fused_tensor)
                probabilities = torch.softmax(logits, dim=1).squeeze()
                predicted_class = torch.argmax(logits, dim=1).item()
            
            emotion = self.emotion_map[predicted_class]
            confidence = probabilities[predicted_class].item()
            
            result = {
                'emotion': emotion,
                'confidence': float(confidence),
                'probabilities': {
                    self.emotion_map[i]: float(probabilities[i])
                    for i in range(4)
                }
            }
            
            logger.info(f"Predicted emotion: {emotion} ({confidence:.2%})")
            return result
        
        finally:
            # Cleanup temporary audio file
            if temp_audio and os.path.exists(temp_audio):
                os.unlink(temp_audio)


# Singleton
_emotion_service_instance = None

def get_emotion_service(checkpoint_path: str = 'checkpoints/at.pth', device: str = 'cuda'):
    global _emotion_service_instance
    
    if _emotion_service_instance is None:
        _emotion_service_instance = EmotionRecognitionService(
            checkpoint_path=checkpoint_path,
            device=device
        )
    
    return _emotion_service_instance
```

---

## Updated Whisper Service (Matches Your MVP)

```python
# services/whisper_service.py (UPDATED to match your stack)
"""
Whisper Transcription - Using 'small' model as in your MVP
"""

import whisper
import torch
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Audio transcription using Whisper 'small' model.
    Matches your MVP spec: 244M params, English-focused.
    """
    
    def __init__(self, model_size: str = 'small', device: str = 'cuda'):
        """
        Initialize Whisper model.
        
        Your MVP uses 'small' model (244M params).
        This is a good balance of speed and accuracy.
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Loading Whisper '{model_size}' model on {self.device}")
        
        try:
            self.model = whisper.load_model(model_size, device=str(self.device))
            logger.info(f"✅ Whisper '{model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper: {e}")
            raise
    
    def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe audio to text.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
        
        Returns:
            {'text': str, 'language': str, 'confidence': float}
        """
        logger.info(f"Transcribing: {audio_path}")
        
        try:
            result = self.model.transcribe(
                audio_path,
                language='en',  # English only as per your MVP
                fp16=(self.device.type == 'cuda'),
                verbose=False
            )
            
            text = result['text'].strip()
            
            logger.info(f"Transcribed: '{text[:50]}...'")
            
            return {
                'text': text,
                'language': result.get('language', 'en'),
                'confidence': 0.9  # Whisper doesn't provide direct confidence
            }
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise


# Singleton
_whisper_service = None

def get_whisper_service(model_size: str = 'small', device: str = 'cuda'):
    """
    Get Whisper service instance.
    Uses 'small' model by default to match your MVP.
    """
    global _whisper_service
    
    if _whisper_service is None:
        _whisper_service = WhisperService(model_size=model_size, device=device)
    
    return _whisper_service
```

---

## Frontend: Video Recording & Upload

```typescript
// src/hooks/useVideoRecorder.ts
import { useState, useRef } from 'react';

export function useVideoRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [duration, setDuration] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timer | null>(null);
  
  const startRecording = async () => {
    try {
      // Request camera + microphone
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,  // Enable video
        audio: true   // Enable audio
      });
      
      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp8,opus'  // WebM format
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        setVideoBlob(blob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(100);  // Collect data every 100ms
      setIsRecording(true);
      setDuration(0);
      
      // Start duration timer
      timerRef.current = setInterval(() => {
        setDuration(d => {
          const newDuration = d + 0.1;
          
          // Auto-stop at 60 seconds
          if (newDuration >= 60) {
            stopRecording();
          }
          
          return newDuration;
        });
      }, 100);
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Could not access camera/microphone');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };
  
  const clearRecording = () => {
    setVideoBlob(null);
    setDuration(0);
  };
  
  return {
    isRecording,
    videoBlob,
    duration,
    startRecording,
    stopRecording,
    clearRecording
  };
}
```

---

## Summary: What Changed

### ✅ Aligned with Your MVP Stack

1. **Whisper:** Using `small` model (244M params) - matches your spec
2. **WavLM:** `microsoft/wavlm-base` (768-dim) - already correct
3. **RoBERTa:** `roberta-base` (768-dim) - already correct
4. **ResNet50:** Available but **NOT USED** in MVP (A+T only)

### ✅ Video Processing Strategy

- **Frontend:** Records video (MediaRecorder API) - uses your existing React stack
- **Upload:** Sends video blob to backend
- **Backend:** Extracts audio from video using ffmpeg or librosa
- **Processing:** Audio + Text emotion detection (skip video frames)

### ✅ No Frontend ML

- All ML processing on backend
- Frontend just records and uploads
- Simpler, more maintainable

### Files to Add:

1. `services/video_processor.py` - Extract audio from video
2. Update `services/emotion_service.py` - Handle video input
3. Update `services/whisper_service.py` - Use 'small' model

**Your existing MVP frontend needs NO CHANGES** - just send video blob instead of audio blob!

