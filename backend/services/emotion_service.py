"""
MECC Emotion Recognition Service
=================================
Handles emotion detection using the ET-TACFN trimodal model.

4-class output based on original model definition:
  0 → happy
  1 → sad
  2 → angry
  3 → neutral
"""

import logging
from typing import Dict, Optional

import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class EmotionRecognitionService:
    """
    Emotion recognition service using ET-TACFN (Audio + Text + Visual).
    """

    def __init__(
        self,
        checkpoint_path: str = "checkpoints/atv_emotion.pth",
        device: str = "cuda",
    ):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing EmotionRecognitionService on {self.device}")

        from models.emotion_classifier import get_ettacfn_model

        logger.info(f"Loading ET-TACFN emotion model from {checkpoint_path}…")
        self.model = get_ettacfn_model(
            checkpoint_path=checkpoint_path,
            device=str(self.device),
        )
        self.model.eval()

        # UPDATED: The exact output order mapping specified by the model description
        self.emotion_map = {0: "happy", 1: "sad", 2: "angry", 3: "neutral"}
        logger.info("✅ EmotionRecognitionService (ET-TACFN) initialized")

    def _to_tensor(self, arr: Optional[np.ndarray], fallback_shape: tuple) -> Optional[torch.Tensor]:
        if arr is None:
            return None
        try:
            t = torch.from_numpy(np.array(arr, dtype=np.float32))
            if t.dim() == 2:
                t = t.unsqueeze(0)
            return t.to(self.device)
        except Exception as e:
            logger.warning(f"_to_tensor failed ({e}), using zeros {fallback_shape}")
            return torch.zeros(fallback_shape, dtype=torch.float32, device=self.device)

    def predict_from_features(
        self,
        audio_features:  Optional[np.ndarray],
        text_features:   Optional[np.ndarray],
        visual_features: Optional[np.ndarray] = None,
    ) -> Dict[str, object]:
        """
        Predict emotion from pre-extracted feature sequences.
        """
        try:
            # Note: Audio fallback shape uses 768 to match WavLM-Base+
            audio_t  = self._to_tensor(audio_features,  fallback_shape=(1, 1,   768))
            text_t   = self._to_tensor(text_features,   fallback_shape=(1, 128, 1024))
            visual_t = self._to_tensor(visual_features, fallback_shape=(1, 30,  256))

            with torch.no_grad():
                logits, _info = self.model(
                    text=text_t,
                    audio=audio_t,
                    visual=visual_t,
                )

                probs      = F.softmax(logits, dim=1)
                confidence, pred_class = torch.max(probs, dim=1)

            emotion_label    = self.emotion_map[pred_class.item()]
            confidence_score = confidence.item()

            logger.info(
                f"Predicted emotion: {emotion_label} "
                f"(confidence: {confidence_score:.2%})"
            )
            return {"emotion": emotion_label, "confidence": confidence_score}

        except Exception as e:
            logger.error(f"EmotionRecognitionService.predict_from_features failed: {e}")
            raise


_emotion_service_instance: Optional[EmotionRecognitionService] = None

def get_emotion_service(
    checkpoint_path: str = "checkpoints/atv_emotion.pth",
    device: str = "cuda",
) -> EmotionRecognitionService:
    global _emotion_service_instance
    if _emotion_service_instance is None:
        _emotion_service_instance = EmotionRecognitionService(
            checkpoint_path=checkpoint_path,
            device=device,
        )
    return _emotion_service_instance