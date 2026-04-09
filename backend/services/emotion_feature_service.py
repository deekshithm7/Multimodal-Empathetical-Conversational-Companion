"""
Emotion Feature Service
=======================
Dedicated feature extraction pipeline for the ET-TACFN emotion model.

Matches the RETRAINED model training pipeline exactly:
  Audio  → WavLM-base       → [T_a, 768]   (microsoft/wavlm-base)
  Text   → RoBERTa-base      → [T_t, 768]   (roberta-base)
  Visual → None → MissingModalityHandler fills in the embedding
              (visual extraction removed; new model trained in audio+text mode)
"""

import os
import logging
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict

import cv2
import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

NUM_VISUAL_FRAMES = 30
TEXT_MAX_LEN      = 128
TARGET_SR         = 16000


class _EmotionAudioEncoder:
    """WavLM-base → [T_a, 768] hidden-state sequence."""

    def __init__(self):
        from transformers import Wav2Vec2FeatureExtractor, AutoModel
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading WavLM-base for emotion feature extraction…")
        
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained("microsoft/wavlm-base")
        self.model = AutoModel.from_pretrained("microsoft/wavlm-base").to(self.device)
        self.model.eval()
        logger.info("✅ WavLM-base loaded")

    @torch.no_grad()
    def encode(self, audio_path: str) -> np.ndarray:
        import soundfile as sf
        import torchaudio

        wav_path = audio_path
        tmp_wav  = None

        try:
            if audio_path.lower().endswith((".webm", ".mp4", ".mkv")):
                tmp_wav = tempfile.mktemp(suffix=".wav")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", audio_path,
                     "-ar", "16000", "-ac", "1", "-vn", "-f", "wav", tmp_wav],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=60, check=True,
                )
                wav_path = tmp_wav

            audio_data, sr = sf.read(wav_path, dtype="float32")
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            if sr != TARGET_SR:
                waveform  = torch.from_numpy(audio_data).unsqueeze(0)
                resampler = torchaudio.transforms.Resample(sr, TARGET_SR)
                audio_data = resampler(waveform).squeeze().numpy()

            inputs = self.processor(
                audio_data,
                sampling_rate=TARGET_SR,
                return_tensors="pt"
            )
            input_values = inputs.input_values.to(self.device)
            outputs      = self.model(input_values)
            return outputs.last_hidden_state.squeeze(0).cpu().numpy().astype(np.float32)

        except Exception as e:
            logger.error(f"EmotionAudioEncoder failed: {e}")
            return np.zeros((1, 768), dtype=np.float32)
        finally:
            if tmp_wav and os.path.exists(tmp_wav):
                try: os.unlink(tmp_wav)
                except Exception: pass


class _EmotionTextEncoder:
    """RoBERTa-base → [T_t, 768] token sequence."""

    def __init__(self):
        from transformers import RobertaTokenizer, RobertaModel
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading RoBERTa-base for emotion feature extraction…")
        
        self.tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
        self.model     = RobertaModel.from_pretrained("roberta-base").to(self.device)
        self.model.eval()
        logger.info("✅ RoBERTa-base loaded")

    @torch.no_grad()
    def encode(self, text: str) -> np.ndarray:
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding="max_length",
                max_length=TEXT_MAX_LEN,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            out    = self.model(**inputs)
            return out.last_hidden_state.squeeze(0).cpu().numpy().astype(np.float32)
        except Exception as e:
            logger.error(f"EmotionTextEncoder failed: {e}")
            return np.zeros((TEXT_MAX_LEN, 768), dtype=np.float32)


class _EmotionVisualEncoder:
    """ResNet50 (avgpool) → Linear(2048, 256) + ReLU → [30, 256]."""

    def __init__(self):
        import torchvision.models as models
        import torchvision.transforms as T

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading ResNet50+proj256 for emotion visual extraction…")

        _resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.feature_extractor = torch.nn.Sequential(
            *list(_resnet.children())[:-1],
            torch.nn.Flatten(),
            torch.nn.Linear(2048, 256),
            torch.nn.ReLU(),
        ).to(self.device)
        self.feature_extractor.eval()

        self.preprocess = T.Compose([
            T.ToPILImage(),
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
        ])
        logger.info("✅ ResNet50+proj256 loaded")

    @torch.no_grad()
    def encode(self, video_path: str) -> np.ndarray:
        tmp_video = None
        target_path = video_path
        try:
            # OpenCV notoriously fails on .webm on many systems. We transcode to mp4 first.
            if video_path.lower().endswith((".webm", ".mkv", ".avi")):
                tmp_video = tempfile.mktemp(suffix=".mp4")
                import subprocess
                # -preset ultrafast -crf 28 means fast conversion, acceptable quality for frame extraction
                subprocess.run(
                    ["ffmpeg", "-y", "-i", video_path,
                     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-an", tmp_video],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=60, check=True,
                )
                target_path = tmp_video

            cap = cv2.VideoCapture(target_path)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {target_path}")

            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 0:
                cap.release()
                return np.zeros((NUM_VISUAL_FRAMES, 256), dtype=np.float32)

            indices = np.linspace(0, total - 1, NUM_VISUAL_FRAMES, dtype=int)
            frames  = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if not ret:
                    frames.append(frames[-1] if frames else np.zeros((224, 224, 3), dtype=np.uint8))
                else:
                    frames.append(frame)
            cap.release()

            tensors = []
            for bgr in frames:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                tensors.append(self.preprocess(rgb))
                
            batch = torch.stack(tensors).to(self.device)
            feats = self.feature_extractor(batch)
            return feats.cpu().numpy().astype(np.float32)

        except Exception as e:
            logger.error(f"EmotionVisualEncoder failed: {e}")
            return np.zeros((NUM_VISUAL_FRAMES, 256), dtype=np.float32)
        finally:
            if tmp_video and os.path.exists(tmp_video):
                try: os.unlink(tmp_video)
                except Exception: pass


# ─────────────────────────────────────────────────────────────────────────────
# Service Class
# ─────────────────────────────────────────────────────────────────────────────

_audio_enc:  Optional[_EmotionAudioEncoder]  = None
_text_enc:   Optional[_EmotionTextEncoder]   = None
_visual_enc: Optional[_EmotionVisualEncoder] = None

def _get_audio_enc():
    global _audio_enc; _audio_enc = _audio_enc or _EmotionAudioEncoder(); return _audio_enc
def _get_text_enc():
    global _text_enc; _text_enc = _text_enc or _EmotionTextEncoder(); return _text_enc
def _get_visual_enc():
    global _visual_enc; _visual_enc = _visual_enc or _EmotionVisualEncoder(); return _visual_enc


class EmotionFeatureService:
    def extract_parallel(self, audio_path=None, text=None, video_path=None):
        futures = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            if audio_path: futures["audio"]  = pool.submit(_get_audio_enc().encode, audio_path)
            if text:       futures["text"]   = pool.submit(_get_text_enc().encode, text)
            if video_path: futures["visual"] = pool.submit(_get_visual_enc().encode, video_path)

        result = {"audio": None, "text": None, "visual": None}
        fallback_shapes = {"audio": (1, 768), "text": (TEXT_MAX_LEN, 1024), "visual": (NUM_VISUAL_FRAMES, 256)}

        for key, fut in futures.items():
            try: result[key] = fut.result()
            except Exception as e:
                logger.error(f"Failed extracting {key}: {e}")
                result[key] = np.zeros(fallback_shapes[key], dtype=np.float32)

        return result

    def preload_encoders(self):
        _get_audio_enc(); _get_text_enc(); _get_visual_enc()
        logger.info("✅ EmotionFeatureService: all encoders pre-loaded")


_emotion_feature_service_instance = None
def get_emotion_feature_service() -> EmotionFeatureService:
    global _emotion_feature_service_instance
    if _emotion_feature_service_instance is None:
        _emotion_feature_service_instance = EmotionFeatureService()
    return _emotion_feature_service_instance