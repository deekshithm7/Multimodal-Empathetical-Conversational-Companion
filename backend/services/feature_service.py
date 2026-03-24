"""
Feature Service - Coordinates Multimodal Feature Extraction

Extracts raw embeddings from up to 3 modalities in parallel:
  Audio  → WavLM    → 768-dim
  Text   → RoBERTa  → 768-dim
  Visual → ResNet50 → 2048-dim

IMPORTANT: This service returns ONLY raw embeddings.
Different downstream models (Emotion MLP, Personality TransformerFusion)
project these internally — do NOT project or reduce here.
"""

import cv2
import numpy as np
import tempfile
import subprocess
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# How many frames to sample from a video for visual features
NUM_FRAMES = 16


class FeatureService:
    """
    Coordinates parallel feature extraction across all modalities.
    Encoders are loaded lazily (singletons shared with personality service).
    """

    def __init__(self):
        self._audio_encoder = None
        self._text_encoder  = None
        self._visual_encoder = None
        self._executor = ThreadPoolExecutor(max_workers=3)
        logger.info("FeatureService initialized")

    # ── Lazy encoder properties ────────────────────────────────────────────────

    @property
    def audio_encoder(self):
        if self._audio_encoder is None:
            from feature_extractors.audio_encoder import get_audio_encoder
            self._audio_encoder = get_audio_encoder()
        return self._audio_encoder

    @property
    def text_encoder(self):
        if self._text_encoder is None:
            from feature_extractors.text_encoder import get_text_encoder
            self._text_encoder = get_text_encoder()
        return self._text_encoder

    @property
    def visual_encoder(self):
        if self._visual_encoder is None:
            from feature_extractors.visual_encoder import get_visual_encoder
            self._visual_encoder = get_visual_encoder()
        return self._visual_encoder

    # ── Internal extraction helpers ────────────────────────────────────────────

    def _extract_audio(self, audio_path: str) -> np.ndarray:
        """Extract 768-dim WavLM embedding from an audio/video file."""
        try:
            import soundfile as sf
            import torch

            wav_path = audio_path
            tmp_wav  = None

            if audio_path.endswith('.webm') or audio_path.endswith('.mp4'):
                tmp_wav  = tempfile.mktemp(suffix='.wav')
                subprocess.run(
                    ['ffmpeg', '-y', '-i', audio_path,
                     '-ar', '16000', '-ac', '1', '-vn', '-f', 'wav', tmp_wav],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=60, check=True
                )
                wav_path = tmp_wav

            audio_data, sr = sf.read(wav_path, dtype='float32')
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            if sr != 16000:
                import torchaudio
                waveform  = torch.from_numpy(audio_data).unsqueeze(0)
                resampler = torchaudio.transforms.Resample(sr, 16000)
                audio_data = resampler(waveform).squeeze().numpy()

            return self.audio_encoder.encode(audio_data).astype(np.float32)

        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return np.zeros(768, dtype=np.float32)
        finally:
            if tmp_wav and os.path.exists(tmp_wav):
                try: os.unlink(tmp_wav)
                except: pass

    def _extract_text(self, text: str) -> np.ndarray:
        """Extract 768-dim RoBERTa embedding from text."""
        try:
            feat = self.text_encoder.encode_text(text)
            return np.array(feat, dtype=np.float32)
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return np.zeros(768, dtype=np.float32)

    def _extract_visual(self, video_path: str) -> np.ndarray:
        """Extract 2048-dim ResNet50 embedding from a video file."""
        tmp_video = None
        target_path = video_path
        try:
            # OpenCV notoriously fails on .webm on many systems. We transcode to mp4 first.
            if video_path.lower().endswith((".webm", ".mkv", ".avi")):
                tmp_video = tempfile.mktemp(suffix=".mp4")
                # -preset ultrafast -crf 28 means fast conversion, acceptable quality for frame extraction
                subprocess.run(
                    ["ffmpeg", "-y", "-i", video_path,
                     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-an", tmp_video],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=60, check=True,
                )
                target_path = tmp_video

            cap   = cv2.VideoCapture(target_path)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {target_path}")

            total   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 0:
                cap.release()
                return np.zeros(2048, dtype=np.float32)

            indices = np.linspace(0, total - 1, NUM_FRAMES, dtype=int)
            frames  = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            cap.release()

            return self.visual_encoder.encode(frames).astype(np.float32)

        except Exception as e:
            logger.error(f"Visual extraction failed: {e}")
            return np.zeros(2048, dtype=np.float32)
        finally:
            if tmp_video and os.path.exists(tmp_video):
                try: os.unlink(tmp_video)
                except Exception: pass

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_parallel(
        self,
        audio_path: Optional[str] = None,
        text:       Optional[str] = None,
        video_path: Optional[str] = None,
    ) -> Dict[str, Optional[np.ndarray]]:
        """
        Extract raw embeddings in parallel from all provided modalities.

        Returns a dict:
          {
            'audio':  np.ndarray (768,)  or None,
            'text':   np.ndarray (768,)  or None,
            'visual': np.ndarray (2048,) or None,
          }

        None means the modality was not requested / no path supplied.
        Downstream models (Emotion, Personality) project internally.
        """
        futures = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            if audio_path:
                futures['audio']  = pool.submit(self._extract_audio, audio_path)
            if text:
                futures['text']   = pool.submit(self._extract_text, text)
            if video_path:
                futures['visual'] = pool.submit(self._extract_visual, video_path)

        result: Dict[str, Optional[np.ndarray]] = {
            'audio':  None,
            'text':   None,
            'visual': None,
        }
        for key, fut in futures.items():
            try:
                result[key] = fut.result()
            except Exception as e:
                logger.error(f"Feature future [{key}] raised: {e}")
                # fallback zeros so callers never get None unexpectedly from a crash
                dims = {'audio': 768, 'text': 768, 'visual': 2048}
                result[key] = np.zeros(dims[key], dtype=np.float32)

        return result

    # ── Legacy compatibility (used by emotion service) ─────────────────────────

    def extract_and_stack_features(
        self,
        audio_path: Optional[str] = None,
        text:       Optional[str] = None,
        image_path: Optional[str] = None,
        use_audio:  bool = True,
        use_text:   bool = True,
        use_visual: bool = False,
    ) -> Dict:
        """
        Legacy method kept for EmotionService compatibility.
        Returns stacked features (concatenated, NOT fused).
        """
        result = self.extract_parallel(
            audio_path=audio_path if use_audio else None,
            text=text            if use_text  else None,
            video_path=image_path if use_visual else None,
        )

        feature_arrays = []
        if use_audio:
            feat = result['audio'] if result['audio'] is not None else np.zeros(768,  dtype=np.float32)
            feature_arrays.append(feat)
        if use_text:
            feat = result['text']  if result['text']  is not None else np.zeros(768,  dtype=np.float32)
            feature_arrays.append(feat)
        if use_visual:
            feat = result['visual'] if result['visual'] is not None else np.zeros(2048, dtype=np.float32)
            feature_arrays.append(feat)

        stacked = np.concatenate(feature_arrays) if feature_arrays else None

        return {
            'audio':     result.get('audio'),
            'text':      result.get('text'),
            'visual':    result.get('visual'),
            'stacked':   stacked,
            'dimension': stacked.shape[0] if stacked is not None else 0,
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_feature_service_instance = None


def get_feature_service() -> FeatureService:
    global _feature_service_instance
    if _feature_service_instance is None:
        _feature_service_instance = FeatureService()
    return _feature_service_instance